$ErrorActionPreference = 'Stop'

$root = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$nginx = Get-Content -Raw -Encoding utf8 (Join-Path $root 'security\nginx\edge.conf.template')
$dockerfile = Get-Content -Raw -Encoding utf8 (Join-Path $root 'security\nginx\Dockerfile')

$required = @(
    'modsecurity on;',
    'modsecurity_rules_file /etc/nginx/modsecurity.d/setup.conf;',
    'ssl_protocols TLSv1.2 TLSv1.3;',
    'proxy_set_header X-Pomerium-Jwt-Assertion '''';',
    'proxy_ssl_verify on;',
    'return 444;',
    'limit_req zone=user_api',
    'limit_req zone=admin_api'
)

$combined = (Get-Content -Raw -Encoding utf8 (Join-Path $root 'security\nginx\nginx.conf')) + $nginx
foreach ($needle in $required) {
    if (-not $combined.Contains($needle)) {
        throw "missing edge security control: $needle"
    }
}

if ($dockerfile -match '(?im)^\s*FROM\s+[^\r\n]*:latest\s*$') {
    throw 'latest image tags are forbidden'
}

if ($nginx -notmatch '\$\{IDENTITY_UPSTREAM\}') {
    throw 'identity upstream handoff variable is missing'
}

if (-not $dockerfile.Contains('RUN /docker-entrypoint.sh /bin/true')) {
    throw 'official CRS templates are not frozen for read-only runtime'
}

Write-Output 'edge static policy: PASS'
