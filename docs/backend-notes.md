# Backend API

| Method | URL | Login | Notes |
|---|---|---|---|
| GET | `/api/health/` | no | checks postgres + redis |
| GET | `/api/accounts/csrf/` | no | call once on page load, sets the csrftoken cookie |
| POST | `/api/accounts/register/` | no | `{"email": "...@fiu.edu", "password": "..."}` |
| POST | `/api/accounts/login/` | no | `{"email", "password"}`, starts a session |
| POST | `/api/accounts/logout/` | yes | |
| GET | `/api/accounts/me/` | yes | the logged in user |
| POST | `/api/crowd-reports/` | yes | `{"location": "<id>", "level": "empty" / "moderate" / "packed"}` |
| GET | `/api/crowd-reports/status/<location_id>/` | no | current crowd level for a location |
| GET | `/api/reviews/?location=<id>` | no | reviews + average rating for a location |
| POST | `/api/reviews/` | yes | `{"location": "<id>", "rating": 1-5, "comment": "..."}` |

Frontend: send requests with `credentials: "include"` (fetch) or `withCredentials: true` (axios), and put the
csrftoken cookie value in an `X-CSRFToken` header on every POST.

- Only @fiu.edu emails can register. Everyone who signs up is a student.
- One review per student per location.
- Crowd reports count for 45 minutes, one per student per location every 10 minutes.
- Reviews and crowd reports never show who posted them.
