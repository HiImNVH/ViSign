"""ai/src/visign_ai/dataset/pilot_owner_assist.py: reuse recorded owner evidence.

Creates a new pilot proposal and partially filled evidence sheet. Existing
attestations are not independent verification or specialist label approval.
"""

import argparse
import hashlib
import json
from pathlib import Path

from .create_splits import assign_groups
from .pilot_review import build_pilot_review, write_csv
from .validate_manifest import audit, read_csv

CONFIRMED_GROUPS = {
    "user-confirmed-shared-source",
    "user-confirmed-independently-recorded-clip",
}


def attested_subset(
    rows: list[dict], inventories: list[dict], rights: list[dict]
) -> tuple[list, list]:
    def indexed(items):
        by_id = {r["sampleId"]: r for r in items}
        if len(by_id) != len(items):
            raise ValueError("duplicate evidence sampleId")
        return by_id

    inventory, rights_by_id = indexed(inventories), indexed(rights)
    indexed(rows)
    selected, decisions = [], []
    for row in rows:
        inv, right = (
            inventory.get(row["sampleId"], {}),
            rights_by_id.get(row["sampleId"], {}),
        )
        if row.get("verificationStatus") == "rejected":
            reason = "rejected-sample-not-selected"
        elif row["sourceUri"] != "dataset:self-recorded":
            reason = "external-source-not-needed-for-owner-only-pilot"
        elif (
            inv.get("sourceUri") != row["sourceUri"]
            or inv.get("sourceReviewStatus") != "user-confirmed-self-recorded"
            or inv.get("classLabel") != row["classLabel"]
            or inv.get("recordingSessionId") != row["recordingSessionId"]
            or inv.get("signerId") != row["signerId"]
            or len(inv.get("sha256", "")) != 64
            or not row["sampleId"].endswith("_" + inv["sha256"][:12])
        ):
            reason = "missing-or-mismatched-owner-source-evidence"
        elif (
            right.get("sourceUri") != row["sourceUri"]
            or right.get("licenseStatus") != "approved"
            or row["licenseStatus"] != "approved"
            or right.get("consentStatus") != "user-declared-approved"
            or right.get("evidenceKind") != "user-attestation-in-chat"
        ):
            reason = "owner-rights-attestation-not-recorded"
        elif inv.get("groupEvidence") not in CONFIRMED_GROUPS:
            reason = "source-group-confirmation-not-recorded"
        else:
            selected.append(dict(row))
            reason = "prior-owner-attestation-reused-for-draft-only"
        decisions.append(
            {
                "sampleId": row["sampleId"],
                "classLabel": row["classLabel"],
                "selectionReason": reason,
                "sourceUri": row["sourceUri"],
                "groupEvidence": inv.get("groupEvidence", ""),
                "labelDecision": "pending-specialist",
                "independentVerification": False,
            }
        )
    return selected, decisions


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "manifest",
        "inventory",
        "rights",
        "registry",
        "classes",
        "dataset-root",
        "quotas",
        "output",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.output.exists():
            raise ValueError("output must be new")
        parent = audit(
            args.manifest, args.registry, args.classes, dataset_root=args.dataset_root
        )
        if not parent["valid"]:
            raise ValueError("parent candidate metadata/hash failed")
        selected, decisions = attested_subset(
            read_csv(args.manifest), read_csv(args.inventory), read_csv(args.rights)
        )
        inventory = {r["sampleId"]: r for r in read_csv(args.inventory)}
        for row in selected:
            digest = hashlib.sha256(
                (args.dataset_root / row["rawPath"]).read_bytes()
            ).hexdigest()
            if digest != inventory[row["sampleId"]]["sha256"]:
                raise ValueError(
                    "full raw hash does not match owner evidence inventory"
                )
        quotas = json.loads(args.quotas.read_text(encoding="utf-8"))
        solution = assign_groups(selected, quotas)
        if solution["status"] != "FEASIBLE":
            raise ValueError("cannot establish structural feasibility")
        original_splits = {r["sampleId"]: r["split"] for r in selected}
        for row in selected:
            row["split"] = solution["assignment"][row["sampleId"]]
        args.output.mkdir(parents=True)
        proposal = args.output / "owner-only.proposal.DRAFT.csv"
        write_csv(proposal, selected)
        write_csv(args.output / "selection-audit.csv", decisions)
        write_csv(
            args.output / "split-change-audit.csv",
            [
                {
                    "sampleId": r["sampleId"],
                    "previousSplit": original_splits[r["sampleId"]],
                    "proposedSplit": r["split"],
                    "metadataOnlyProposal": True,
                }
                for r in selected
            ],
        )
        package = args.output / "pilot-review"
        summary = build_pilot_review(
            proposal,
            args.registry,
            args.classes,
            args.dataset_root,
            package,
            {r["meaningId"] for r in selected},
        )
        assisted = read_csv(package / "sample-review.csv")
        for row in assisted:
            # These fields record evidence collection, not approval on behalf of a reviewer.
            row.update(
                labelDecision="pending-specialist",
                rightsDecision="prior-owner-attestation-recorded",
                rightsEvidenceReference="rights snapshot joined by sampleId; owner declaration 2026-11-07",
                groupDecision="prior-user-group-confirmation-recorded",
                groupEvidenceReference=inventory[row["sampleId"]]["groupEvidence"],
                reviewer="automated-evidence-collection",
                notes="No new consent, label, signer identity or class approval inferred",
            )
        write_csv(package / "sample-review.ASSISTED.csv", assisted)
        checksums = {
            name: hashlib.sha256(path.read_bytes()).hexdigest()
            for name, path in (
                ("parentManifestSha256", args.manifest),
                ("inventorySha256", args.inventory),
                ("rightsSha256", args.rights),
                ("quotasSha256", args.quotas),
            )
        }
        with (args.output / "evidence-basis.json").open(
            "x", encoding="utf-8", newline="\n"
        ) as stream:
            stream.write(
                json.dumps(
                    {
                        **checksums,
                        "retained": len(selected),
                        "excluded": len(decisions) - len(selected),
                        "pilotDataGatePassed": summary["pilotDataGatePassed"],
                        "humanApprovalsCreated": False,
                    },
                    indent=2,
                )
                + "\n"
            )
    except (ValueError, OSError, KeyError, TypeError):
        print(
            "Owner-assist preparation failed; check input evidence, quotas and new output directory"
        )
        return 1
    print(
        json.dumps(
            {
                "proposalCreated": True,
                "retained": len(selected),
                "pilotDataGatePassed": summary["pilotDataGatePassed"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
