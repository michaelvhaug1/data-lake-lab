-- Run as ACCOUNTADMIN. Creates a non-interactive service user for dbt / Python.
-- This is standard practice (pipelines never run as a person), and it sidesteps the
-- case-sensitive username that Google sign-in created.
USE ROLE ACCOUNTADMIN;

CREATE USER IF NOT EXISTS LAKE_SVC
  TYPE = SERVICE
  DEFAULT_ROLE = LAKE_DEV
  DEFAULT_WAREHOUSE = LAKE_WH
  DEFAULT_NAMESPACE = LAKE.DEV
  COMMENT = 'data-lake-lab pipeline user (key-pair auth from laptop)';

ALTER USER LAKE_SVC SET RSA_PUBLIC_KEY = 'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAlYr9bn1CPd1nER9bBjw4CKwN55b9ZqmhA8MNoM/z7v3PWe036/pM1KBk03fCXxCh0RD8j3evxftH1FUmZmyjnoKv+pNINLMhCfgSKy9VGjsVVu1wz2VutBJ6hue9VNfCRKdtvrEohrLFhRCXEfKApYx93WsBXNFkjgO+yIFihXzRQeczuh/PI4//ZjepfGNNDu+XVnCYsmW3i5tjqo+5zSWnEheCMhezMvfg0EJfTqZCODTs8rthbUx4+bJstZXTRJZdnFTWeDNCOHHUUq3YfYfh59Ze3pypgf3JPHzTvgYOc4fji/runeQH3P5JQ2UtS9c0kmNixfkN7KxE0nM8CwIDAQAB';

GRANT ROLE LAKE_DEV TO USER LAKE_SVC;

-- Optional: take the key back off your personal login now that the service user has it.
ALTER USER "michaelvhaug" UNSET RSA_PUBLIC_KEY;

DESC USER LAKE_SVC;
