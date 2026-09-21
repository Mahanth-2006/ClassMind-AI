# ClassMind frontend

Run `npm install`, copy `.env.example` to `.env.local`, then run `npm run dev`.

The student client posts `POST /engagement` and connects to `NEXT_PUBLIC_WS_URL` with `room` and `student` query parameters. The teacher dashboard reads `GET /classrooms/DEMO-101/engagement`. Update these paths when Person B shares the final REST and WebSocket contract.
