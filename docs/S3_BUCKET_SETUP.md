# AWS S3 Bucket Setup Guide for AudioPoster

## 🚨 Critical S3 Configuration Requirements

The AudioPoster application requires specific S3 bucket permissions to function properly. This guide provides the complete setup needed.

## 📋 Required S3 Bucket Configuration

### 1. Bucket Creation
- **Bucket Name**: `audioposter-bucket` (or your preferred name)
- **Region**: `us-east-2` (must match your environment configuration)
- **Versioning**: Enabled (recommended for data protection)

### 2. Block Public Access Settings
**IMPORTANT**: You must disable these block public access settings for preview files to work:

- ❌ Block all public access
- ❌ Block public access to buckets and objects granted through new access control lists (ACLs)
- ❌ Block public access to buckets and objects granted through any access control lists (ACLs)
- ❌ Block public access to buckets and objects granted through new public bucket or ownership policies
- ❌ Block public access to buckets and objects granted through any public bucket or ownership policies

**Note**: This is safe because we only make specific files public (preview PDFs, photos, waveforms) and use proper ACLs.

### 3. Object Ownership Settings
**CRITICAL**: You must enable ACLs for the bucket to work properly:

- **Object Ownership**: Set to "Bucket owner preferred" (NOT "Bucket owner enforced")
- **ACLs**: Enable "ACLs disabled" to be OFF
- **Bucket owner preferred**: This allows ACLs while maintaining security

**Why this matters**: If ACLs are disabled, you'll get "AccessControlListNotSupported" errors when uploading files.

### 4. Bucket Policy
Apply this bucket policy to allow public read access to preview files:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadForPreviewFiles",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::audioposter-bucket/*"
        },
        {
            "Sid": "AllowAuthenticatedUsers",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::YOUR_ACCOUNT_ID:user/YOUR_IAM_USER"
            },
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::audioposter-bucket",
                "arn:aws:s3:::audioposter-bucket/*"
            ]
        }
    ]
}
```

**Important**: This policy makes ALL objects publicly readable. Since you're using ACLs to control access, this is safe because:
1. **Preview files** are uploaded with `ACL: public-read` (intentionally public)
2. **Final files** are uploaded with `ACL: private` (remain private)
3. **ACLs override bucket policies** for access control

### Alternative: More Restrictive Policy (Optional)
If you want more granular control, you can use this policy instead:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadForPreviewFiles",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": [
                "arn:aws:s3:::audioposter-bucket/pdfs/preview.pdf",
                "arn:aws:s3:::audioposter-bucket/photos/*",
                "arn:aws:s3:::audioposter-bucket/waveforms/*"
            ]
        },
        {
            "Sid": "AllowAuthenticatedUsers",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::YOUR_ACCOUNT_ID:user/YOUR_IAM_USER"
            },
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::audioposter-bucket",
                "arn:aws:s3:::audioposter-bucket/*"
            ]
        }
    ]
}
```

This alternative policy only allows public read access to specific folders where preview files are stored.

**Replace**:
- `audioposter-bucket` with your actual bucket name
- `YOUR_ACCOUNT_ID` with your AWS account ID
- `YOUR_IAM_USER` with your IAM username

### 5. IAM User Permissions
Your IAM user needs these permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket",
                "s3:GetBucketLocation",
                "s3:GetObjectAcl"
            ],
            "Resource": [
                "arn:aws:s3:::audioposter-bucket",
                "arn:aws:s3:::audioposter-bucket/*"
            ]
        }
    ]
}
```

## 🔧 Application Configuration

### Environment Variables
Ensure these are set in your `.env` file or Docker environment:

```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET=audioposter-bucket
S3_REGION=us-east-2
```

### Docker Compose Configuration
Your `docker-compose.yml` should include:

```yaml
services:
  api:
    environment:
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - S3_BUCKET=${S3_BUCKET}
      - S3_REGION=${S3_REGION}
  
  celery-worker:
    environment:
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - S3_BUCKET=${S3_BUCKET}
      - S3_REGION=${S3_REGION}
```

## 📁 File Access Patterns

### Public Files (ACL: public-read)
These files are made publicly accessible for preview functionality:

1. **Preview PDFs**: `pdfs/preview.pdf`
2. **Photos**: `photos/{session_token}.jpg`
3. **Waveforms**: `waveforms/{session_token}.png`

### Private Files (ACL: private)
These files remain private and require authentication:

1. **Final PDFs**: `pdfs/{order_id}.pdf`
2. **Permanent Audio**: `permanent_audio/{hash}.mp3`

## 🚀 Testing S3 Configuration

### 1. Test File Upload
```bash
# Check if files are being uploaded with correct ACLs
aws s3api get-object-acl --bucket audioposter-bucket --key photos/test.jpg
```

### 2. Test Public Access
```bash
# Test if preview files are publicly accessible
curl -I "https://audioposter-bucket.s3.us-east-2.amazonaws.com/pdfs/preview.pdf"
```

### 3. Check Bucket Policy
```bash
# Verify bucket policy is applied
aws s3api get-bucket-policy --bucket audioposter-bucket
```

## 🐛 Common S3 Issues & Solutions

### Issue 1: 403 Forbidden Error
**Symptoms**: `Failed to load resource: the server responded with a status of 403 (Forbidden)`

**Causes**:
- Block public access is enabled
- Bucket policy is missing or incorrect
- ACL is not set to public-read

**Solutions**:
1. Disable block public access settings
2. Apply correct bucket policy
3. Ensure files are uploaded with `ACL: public-read`

### Issue 2: Access Denied on Upload
**Symptoms**: `An error occurred (AccessDenied) when calling the PutObject operation`

**Causes**:
- IAM user lacks required permissions
- Bucket policy blocks uploads
- Incorrect AWS credentials

**Solutions**:
1. Verify IAM user permissions
2. Check bucket policy allows authenticated users
3. Verify AWS credentials in environment

### Issue 3: Region Mismatch
**Symptoms**: `Error parsing the X-Amz-Credential parameter; the region 'us-east-1' is wrong; expecting 'us-east-2'`

**Causes**:
- Environment variable `S3_REGION` is incorrect
- Hardcoded region in code

**Solutions**:
1. Set `S3_REGION=us-east-2` in environment
2. Restart Docker services after changing environment

### Issue 4: AccessControlListNotSupported Error
**Symptoms**: `An error occurred (AccessControlListNotSupported) when calling the PutObject operation: The bucket does not allow ACLs`

**Causes**:
- S3 bucket has Object Ownership set to "Bucket owner enforced"
- ACLs are disabled for the bucket

**Solutions**:
1. Change Object Ownership to "Bucket owner preferred"
2. Enable ACLs in bucket settings
3. Ensure bucket policy allows public read access
4. See detailed setup steps above

## 🔒 Security Considerations

### What's Public
- **Preview PDFs**: Temporary files with watermarks
- **Photos**: User-uploaded images (consider privacy implications)
- **Waveforms**: Audio visualization data

### What's Private
- **Final PDFs**: Paid content without watermarks
- **Audio Files**: User audio content
- **Order Data**: Payment and user information

### Recommendations
1. **Use CloudFront**: For production, consider using CloudFront with S3 for better performance and security
2. **Lifecycle Policies**: Set up S3 lifecycle policies to automatically delete old preview files
3. **Monitoring**: Enable CloudTrail to monitor S3 access patterns
4. **Regular Audits**: Periodically review public file access

## 📚 Additional Resources

- [AWS S3 Block Public Access](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html)
- [S3 Bucket Policies](https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-policies.html)
- [S3 Object ACLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/acl-overview.html)
- [IAM Policies for S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-with-s3-actions.html)

---

## 🎯 Quick Setup Checklist

- [ ] Create S3 bucket in us-east-2 region
- [ ] Disable all block public access settings
- [ ] **Set Object Ownership to "Bucket owner preferred" (enable ACLs)**
- [ ] Apply bucket policy for public read access
- [ ] Configure IAM user with proper permissions
- [ ] Set environment variables in Docker
- [ ] Test file upload and public access
- [ ] Verify preview PDFs load without 403 errors
- [ ] Verify no "AccessControlListNotSupported" errors

**Remember**: The key to fixing the 403 error is ensuring that preview files are uploaded with `ACL: public-read` and that the bucket allows public read access for objects with this ACL.
