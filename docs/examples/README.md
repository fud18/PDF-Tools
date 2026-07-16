# Examples

## Inspect PDF

```bash
curl -H "X-API-Key: <key>"   -F "file=@document.pdf"   https://server/v1/pdf/inspect
```

## Fill PDF

```bash
curl -H "X-API-Key: <key>"   -F "file=@form.pdf"   -F 'fields={"Name":"Example"}'   https://server/v1/pdf/fill
```
