# ViSign AWS infrastructure

> **Trạng thái 2026-11-07: kế hoạch, chưa triển khai.** Nhóm chốt hoàn thiện bản chạy local trước;
> chưa tạo stack, tài nguyên hay credential AWS nào. Trước khi Submit stack OIDC, kiểm tra lại điều
> kiện `token.actions.githubusercontent.com:ref` có được IAM hỗ trợ; nếu workflow không assume được
> role thì bỏ điều kiện này và dựa vào branch policy của environment `production`. Instance size chốt
> theo benchmark T095 (đỉnh 480–600 MB/clip trên Windows), không mặc định gói 1 GB.

Production target: AWS `ap-southeast-2`, CloudFront + one EC2 host, private ECR/S3, SSM and
CloudWatch. AWS Free Plan must not be upgraded without explicit owner approval.

## Permission split

- Account owner/Huy: root MFA, billing, budgets, IAM/OIDC bootstrap and foundational infrastructure.
- Tín/P2: application deployment through the protected GitHub `production` environment.
- EC2: instance role reads only the approved model-artifact prefix and writes approved logs.
- No member receives the root password, a payment method or a long-lived AWS access key.

## Bootstrap GitHub OIDC

Template: `cloudformation/bootstrap-github-oidc.yml`.

The stack creates only:

1. The GitHub Actions OIDC provider.
2. `ViSignGitHubDeployRole`, trusted only for:
   - repository `HiImNVH/ViSign`;
   - GitHub environment `production`;
   - branch `main`.

The role can push `visign-*` ECR images and S3 artifacts, send an SSM command only to production
instances tagged `Project=ViSign`, read `visign-*` stack outputs and invalidate a CloudFront
distribution tagged `Project=ViSign`. It cannot create IAM users/access keys, change billing, join
AWS Organizations or create foundational infrastructure.

CloudFormation console parameters:

| Parameter | Value |
|---|---|
| Stack name | `visign-github-oidc` |
| Region | `ap-southeast-2` |
| `GitHubOwner` | `HiImNVH` |
| `GitHubRepository` | `ViSign` |
| `GitHubBranch` | `main` |
| `GitHubEnvironment` | `production` |

Creating the stack requires acknowledging `CAPABILITY_NAMED_IAM`. Review the template and request
the account owner's action-time confirmation before selecting **Submit**.

## GitHub environment

Create a repository environment named `production` and restrict deployment branches to `main`.
Require the account owner/Huy as reviewer when the GitHub plan supports required reviewers. Store:

- Variable `AWS_REGION=ap-southeast-2`.
- Variable `AWS_DEPLOY_ROLE_ARN=<GitHubDeployRoleArn stack output>`.

The role ARN is an identifier rather than a secret, but it must not be mixed with credentials. Do not
create `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY` repository secrets.

## Verification gate

Before Tín receives deployment control:

- Confirm root MFA is enabled.
- Confirm the OIDC trust shows the exact repo, environment and branch conditions.
- Confirm no IAM user or access key was created.
- Run a GitHub workflow containing `aws sts get-caller-identity` and confirm the assumed role is
  `ViSignGitHubDeployRole`.
- Confirm the workflow cannot deploy without `production` environment approval.
- Record stack ID, role ARN, workflow run and reviewer result in the CP7 evidence; never record tokens.
