# Verified API Endpoints Reference

Last verified: 2025-01-17

## ✅ Verified and Correct Endpoints

### Senso
- **Base URL**: `https://sdk.senso.ai/api/v1` ✅
- **Auth**: Bearer token using `SENSO_KEY`
- **Status**: CORRECT

### Airia
- **Base URL**: `https://api.airia.ai/v1` ✅
- **Docs**: `https://api.airia.ai/docs/`
- **Status**: CORRECT

### OpenAI
- **Base URL**: Handled by SDK (api.openai.com)
- **Auth**: API key in Authorization header
- **Status**: CORRECT (SDK handles endpoint)

### Snowflake
- **Format**: `https://<account>.snowflakecomputing.com/api/v2`
- **Auth**: JWT token
- **Status**: CORRECT (uses SDK)

### Redpanda/Kafka
- **Broker**: `localhost:9092` (default)
- **REST API**: `localhost:8082` (Pandaproxy)
- **Status**: CORRECT

## ⚠️ Updated Endpoints (Fixed)

### Intercom
- **OLD**: `https://api-iam.intercom.io` ❌
- **NEW**: `https://api.intercom.io` ✅
- **Regional Options**:
  - US: `https://api.intercom.io`
  - EU: `https://api.eu.intercom.io`
  - AU: `https://api.au.intercom.io`
- **Auth**: Bearer token

### TrueFoundry
- **OLD**: `https://api.truefoundry.com` ❌
- **NEW**: `https://your-control-plane.truefoundry.com/api/llm` ✅
- **Note**: Replace `your-control-plane` with actual control plane URL
- **Auth**: API key + `x-tfy-provider-name` header

## 📝 Additional API Details

### Stripe
- **Base URL**: `https://api.stripe.com/v1`
- **V2 API**: `https://api.stripe.com/v2` (newer endpoints)
- **Auth**: Bearer token with secret key
- **Format**: Form-encoded requests, JSON responses

### Twilio
- **Base URL**: `https://api.twilio.com/2010-04-01`
- **Auth**: HTTP Basic (Account SID as username, Auth Token as password)
- **Note**: Different products may have different base URLs

### Segment
- **Public API**: `https://api.segmentapis.com`
- **HTTP Tracking**: `https://api.segment.io/v1/` (US)
- **EU Tracking**: `https://events.eu1.segmentapis.com`
- **Config API**: `https://platform.segmentapis.com`
- **Auth**: Bearer token

### Sentry
- **Base URL**: `https://sentry.io/api/0/` (US)
- **DE Region**: `https://de.sentry.io/api/0/`
- **Ingest**: `https://<key>@<org>.ingest.sentry.io/<project>`
- **Auth**: Bearer token

### ElevenLabs
- **Base URL**: `https://api.elevenlabs.io`
- **TTS Endpoint**: `/v1/text-to-speech/{voice_id}`
- **Auth**: `xi-api-key` header

## 🔐 Authentication Summary

| API | Auth Method | Header/Format |
|-----|------------|---------------|
| **Senso** | Bearer Token | `Authorization: Bearer <token>` |
| **Airia** | API Key | Check docs for header format |
| **OpenAI** | API Key | `Authorization: Bearer sk-...` |
| **Intercom** | Bearer Token | `Authorization: Bearer <token>` |
| **Stripe** | Bearer Token | `Authorization: Bearer sk_...` |
| **Twilio** | Basic Auth | Base64(SID:AuthToken) |
| **Segment** | Bearer Token | `Authorization: Bearer <token>` |
| **Sentry** | Bearer Token | `Authorization: Bearer <token>` |
| **ElevenLabs** | Custom Header | `xi-api-key: <key>` |
| **Snowflake** | JWT | `Authorization: Bearer <jwt>` |
| **TrueFoundry** | API Key | Custom headers required |

## 🌍 Regional Considerations

Some APIs offer regional endpoints for data residency:

1. **Intercom**: US, EU, AU regions
2. **Segment**: US, EU regions  
3. **Sentry**: US, DE regions

Choose the appropriate region based on:
- Data residency requirements
- GDPR compliance needs
- Latency optimization

## 📚 Documentation Links

- **Intercom**: https://developers.intercom.com/docs
- **Stripe**: https://stripe.com/docs/api
- **Twilio**: https://www.twilio.com/docs
- **Segment**: https://segment.com/docs/connections/sources/catalog/
- **Sentry**: https://docs.sentry.io/api/
- **ElevenLabs**: https://elevenlabs.io/docs/api-reference
- **Snowflake**: https://docs.snowflake.com/en/developer-guide/sql-api/
- **TrueFoundry**: https://docs.truefoundry.com/
- **Airia**: https://api.airia.ai/docs/
- **Senso**: Contact vendor for documentation