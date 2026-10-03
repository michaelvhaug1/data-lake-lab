-- Run in Snowsight (as yourself). Registers the lab laptop's key for key-pair auth,
-- so dbt / Python connect without a password or MFA prompt.
ALTER USER "michaelvhaug" SET RSA_PUBLIC_KEY = 'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAlYr9bn1CPd1nER9bBjw4CKwN55b9ZqmhA8MNoM/z7v3PWe036/pM1KBk03fCXxCh0RD8j3evxftH1FUmZmyjnoKv+pNINLMhCfgSKy9VGjsVVu1wz2VutBJ6hue9VNfCRKdtvrEohrLFhRCXEfKApYx93WsBXNFkjgO+yIFihXzRQeczuh/PI4//ZjepfGNNDu+XVnCYsmW3i5tjqo+5zSWnEheCMhezMvfg0EJfTqZCODTs8rthbUx4+bJstZXTRJZdnFTWeDNCOHHUUq3YfYfh59Ze3pypgf3JPHzTvgYOc4fji/runeQH3P5JQ2UtS9c0kmNixfkN7KxE0nM8CwIDAQAB';

-- Verify: the RSA_PUBLIC_KEY_FP row should now have a SHA256:... value.
DESC USER "michaelvhaug";
