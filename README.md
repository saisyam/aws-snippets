# AWS Snippets
This repo contains code snippets for working with various AWS services. Below is the list of snippets along with a short description.

## AWS Authentication
With AWS Signature Version 4, there are two ways to generate the authentication request:
1. [Using Authorization Header](https://docs.aws.amazon.com/AmazonS3/latest/API/sigv4-auth-using-authorization-header.html)
2. [Using Query Parameters](https://docs.aws.amazon.com/AmazonS3/latest/API/sigv4-query-string-auth.html)

## S3 GET using query parameters authentication
In this example, we use the second approach. I implemented this using Python3. The code is available [here](https://github.com/saisyam/aws-snippets/blob/main/s3-get-mfa.py).

## S3 PUT using query parameters authentication
S3 PUT implementation using Query parameters authentication. The code is available [here](https://github.com/saisyam/aws-snippets/blob/main/s3-put-mfa.py)