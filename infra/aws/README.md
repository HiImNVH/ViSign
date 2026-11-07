# ViSign AWS infrastructure

> **Trạng thái 2026-11-07: OIDC bị chặn, chưa có workload production.** Stack
> `visign-github-oidc` đã được thử tại `ap-southeast-2` nhưng `GitHubActionsOidcProvider` nhận
> `403` do AWS-managed Service Control Policy từ chối `iam:CreateOpenIDConnectProvider`.
> CloudFormation kết thúc `ROLLBACK_COMPLETE`; provider có trạng thái `DELETE_COMPLETE`, không tạo
> deploy role hay credential. Không retry và không nâng Paid Plan/activate Advanced Features nếu chưa
> có phê duyệt riêng của owner. Instance size vẫn phải chốt theo benchmark T095 (đỉnh 480–600 MB/clip
> trên Windows), không mặc định gói 1 GB.

Attempt evidence: `docs/evidence/checkpoints/CP7/T096-aws-access-bootstrap.md`.

Production target: AWS `ap-southeast-2`, CloudFront + one EC2 host, private ECR/S3, SSM and
CloudWatch. AWS Free Plan must not be upgraded without explicit owner approval.

## Permission split

- Account owner/Huy: billing, spend boundary, IAM/OIDC decision and foundational infrastructure.
- Tín/P2: đã chấp nhận lời mời AWS Settings vào project `Rubber Ducking`; có thể triển khai thủ công
  bằng phiên đăng nhập của chính Tín trong Console/CloudShell, nhưng không có quyền billing/team admin.
- GitHub `production` deployment chỉ mở sau khi OIDC được phép và quality gate T091 đạt.
- EC2: instance role reads only the approved model-artifact prefix and writes approved logs.
- No member receives the root password, a payment method or a long-lived AWS access key.

## Bootstrap GitHub OIDC

Template: `cloudformation/bootstrap-github-oidc.yml`.

**Blocker hiện tại**: Free Plan project áp SCP do AWS quản lý nên template không thể tạo OIDC
provider. Template được giữ làm phương án tương lai; không được đổi sang IAM user/access key để lách
blocker. Manual Console/CloudShell deployment bằng phiên của Tín chỉ là đường tích hợp tạm thời và
không được tính là hoàn thành automated deploy gate T091/T096.

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

Nếu blocker được gỡ bằng một quyết định đã phê duyệt, việc retry stack vẫn yêu cầu acknowledge
`CAPABILITY_NAMED_IAM`, review lại template và xin xác nhận action-time trước **Submit**.

## GitHub environment

Chỉ thực hiện mục này sau khi OIDC được mở khóa. Create a repository environment named `production`
and restrict deployment branches to `main`.
Require the account owner/Huy as reviewer when the GitHub plan supports required reviewers. Store:

- Variable `AWS_REGION=ap-southeast-2`.
- Variable `AWS_DEPLOY_ROLE_ARN=<GitHubDeployRoleArn stack output>`.

The role ARN is an identifier rather than a secret, but it must not be mixed with credentials. Do not
create `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY` repository secrets.

## Verification gate

Before automated deployment control is enabled:

- Confirm root MFA is enabled.
- Confirm the OIDC trust shows the exact repo, environment and branch conditions.
- Confirm no IAM user or access key was created.
- Run a GitHub workflow containing `aws sts get-caller-identity` and confirm the assumed role is
  `ViSignGitHubDeployRole`.
- Confirm the workflow cannot deploy without `production` environment approval.
- Record stack ID, role ARN, workflow run and reviewer result in the CP7 evidence; never record tokens.

## Temporary manual deployment boundary

- Tín đăng nhập bằng AWS Builder ID của chính mình và chọn project `Rubber Ducking`.
- Chỉ deploy commit đã qua quality gate; ghi commit SHA, lệnh/thao tác, resource ID và smoke result.
- Không chia sẻ session, root/password, payment method, access key hoặc secret qua chat/repository.
- Không tạo EC2/EIP/ECR/S3/CloudFront trước T095 và xác nhận riêng về phạm vi tài nguyên/credit.
- Manual deployment không thay thế yêu cầu OIDC/least privilege; T091 và T096 giữ trạng thái mở.
