# AWS S3 put using Query parameters with MFA token

import sys, os, base64, datetime, hashlib, hmac, urllib, subprocess
import requests
import mimetypes

# Key derivation functions. See:
# http://docs.aws.amazon.com/general/latest/gr/signature-v4-examples.html#signature-v4-examples-python
def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

def getSignatureKey(key, dateStamp, regionName, serviceName):
    kDate = sign(('AWS4' + key).encode('utf-8'), dateStamp)
    kRegion = sign(kDate, regionName)
    kService = sign(kRegion, serviceName)
    kSigning = sign(kService, 'aws4_request')
    return kSigning

# Get environment variables
key_id = subprocess.run(['aws', 'configure', 'get', 'aws_access_key_id'], stdout=subprocess.PIPE)
access_key = key_id.stdout.decode('utf-8').strip()
secret = subprocess.run(['aws', 'configure', 'get', 'aws_secret_access_key'], stdout=subprocess.PIPE)
secret_key = secret.stdout.decode('utf-8').strip()
session = subprocess.run(['aws', 'configure', 'get', 'aws_session_token'], stdout=subprocess.PIPE)
session_token = session.stdout.decode('utf-8').strip()

if access_key is None or secret_key is None or session_token is None:
    print("Make sure all environment variales are set - \nAWS_ACCESS_KEY_ID\nAWS_SECRET_ACCESS_KEY\nAWS_SESSION_TOKEN")
    sys.exit()

if len(sys.argv) < 2:
    print("Usage: python3 s3-put-mfa <S3 URL> <file> <region - optional>")
    print("Region is optional, default is us-east-1")
    sys.exit()

# ************* TASK 1: CREATE A CANONICAL REQUEST *************
# http://docs.aws.amazon.com/general/latest/gr/sigv4-create-canonical-request.html

# Step 1: Define the verb (GET, POST, etc.)
method = 'PUT' 
service = 's3'
region = 'us-east-1'

# Step 2: Create canonical URI--the part of the URI from domain to query 
# string (use '/' if no path)
file_to_upload = sys.argv[2]
mt = mimetypes.MimeTypes()
content_type = mt.guess_type(file_to_upload)[0]
file_stats = os.stat(file_to_upload)
content_length = file_stats.st_size
headers = {
    'Content-Type': content_type,
    'Content-Length': str(content_length)
}

s3_url = sys.argv[1]
parsed_url = urllib.parse.urlparse(s3_url)
if len(sys.argv) == 4:
    region = sys.argv[3]
host = parsed_url.netloc
canonical_uri = parsed_url.path

# Step 3: Create the canonical headers and signed headers. Header names
# must be trimmed and lowercase, and sorted in code point order from
# low to high. Note trailing \n in canonical_headers.
# signed_headers is the list of headers that are being included
# as part of the signing process. For requests that use query strings,
# only "host" is included in the signed headers.
canonical_headers = 'host:' + host + '\n'
signed_headers = 'host'

# Match the algorithm to the hashing algorithm you use, either SHA-1 or
# SHA-256 (recommended)
# Create a date for headers and the credential string
t = datetime.datetime.utcnow()
amz_date = t.strftime('%Y%m%dT%H%M%SZ') # Format date as YYYYMMDD'T'HHMMSS'Z'
datestamp = t.strftime('%Y%m%d') # Date w/o time, used in credential scope
algorithm = 'AWS4-HMAC-SHA256'
credential_scope = datestamp + '/' + region + '/' + service + '/' + 'aws4_request'

# Step 4: Create the canonical query string. In this example, request
# parameters are in the query string. Query string values must
# be URL-encoded (space=%20). The parameters must be sorted by name.
# use session_token for MFA enabled logins
canonical_querystring = 'X-Amz-Algorithm=AWS4-HMAC-SHA256'
canonical_querystring += '&X-Amz-Credential=' + urllib.parse.quote_plus(access_key + '/' + credential_scope)
canonical_querystring += '&X-Amz-Date=' + amz_date
canonical_querystring += '&X-Amz-Expires=86400'
canonical_querystring += '&X-Amz-Security-Token=' + urllib.parse.quote_plus(session_token)
canonical_querystring += '&X-Amz-SignedHeaders=' + signed_headers

# Step 5: Create payload hash. For GET requests, the payload is an
# empty string ("").
payload_hash = hashlib.sha256(('').encode('utf-8')).hexdigest()

# Step 6: Combine elements to create canonical request
canonical_request = method + '\n' + canonical_uri + '\n' + canonical_querystring + '\n' + canonical_headers + '\n' + signed_headers + '\nUNSIGNED-PAYLOAD'

# ************* TASK 2: CREATE THE STRING TO SIGN*************
string_to_sign = algorithm + '\n' +  amz_date + '\n' +  credential_scope + '\n' +  hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()

# ************* TASK 3: CALCULATE THE SIGNATURE *************
# Create the signing key
signing_key = getSignatureKey(secret_key, datestamp, region, service)

# Sign the string_to_sign using the signing_key
signature = hmac.new(signing_key, (string_to_sign).encode("utf-8"), hashlib.sha256).hexdigest()

# ************* TASK 4: ADD SIGNING INFORMATION TO THE REQUEST *************
# The auth information can be either in a query string
# value or in a header named Authorization. This code shows how to put
# everything into a query string.
canonical_querystring += '&X-Amz-Signature=' + signature 


# ************* SEND THE REQUEST *************
# The 'host' header is added automatically by the Python 'request' lib. But it
# must exist as a header in the request.
request_url = s3_url + "?" + canonical_querystring

print('\nBEGIN REQUEST++++++++++++++++++++++++++++++++++++')
print('Request URL = ' + request_url)
with open(file_to_upload, 'rb') as data:
    r = requests.put(request_url, data=data, headers=headers)
    print('\nRESPONSE++++++++++++++++++++++++++++++++++++')
    print('Response code: %d\n' % r.status_code)
    print(r.text)


