import asyncio
import json
import httpx
import websockets

async def run_live_e2e_tests():
    print("=" * 60)
    print("VOXGUARD LIVE SYSTEM VERIFICATION")
    print("=" * 60)

    # 1. Test Backend Health Endpoint
    async with httpx.AsyncClient() as client:
        res = await client.get("http://127.0.0.1:8000/health")
        assert res.status_code == 200, f"Health check failed: {res.status_code}"
        assert res.json() == {"status": "ok"}
        print(" [PASS] Backend Health Check: http://127.0.0.1:8000/health -> 200 OK")

    # 2. Test Frontend Next.js Landing Page
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get("http://127.0.0.1:3000")
        assert res.status_code == 200, f"Frontend landing page failed: {res.status_code}"
        assert "Call risk monitor" in res.text or "voxguard" in res.text.lower()
        print(" [PASS] Frontend Next.js Server: http://127.0.0.1:3000 -> 200 OK")

    # 3. Test Contract Endpoint
    async with httpx.AsyncClient() as client:
        res = await client.get("http://127.0.0.1:8000/contract")
        assert res.status_code == 200, f"Contract endpoint failed: {res.status_code}"
        data = res.json()
        assert "rolling_risk_score" in data and "alert_level" in data
        print(" [PASS] Strict Data Contract API: http://127.0.0.1:8000/contract -> 200 OK")

    # 4. Test WebSocket Real-Time Stream & Live Simulation
    ws_uri = "ws://127.0.0.1:8000/ws/session"
    print(f"Connecting to WebSocket: {ws_uri} ...")
    
    async with websockets.connect(ws_uri) as ws:
        connected_msg = await ws.recv()
        connected_data = json.loads(connected_msg)
        assert connected_data.get("event") == "connected"
        print(" [PASS] WebSocket Handshake connected successfully:", connected_data)

        # 5. Start Call Simulation with Unknown Contact + OTP request context
        sim_payload = {
            "file_path": "data/sample_calls/demo_call.wav",
            "chunk_duration_sec": 3.0,
            "delay_sec": 0.5,
            "scenario": "gradual_escalation",
            "context": {
                "caller_context": "unknown_contact",
                "transaction_type": "otp_or_pin_request",
                "user_confirmation_required": True
            }
        }
        
        async with httpx.AsyncClient() as client:
            start_res = await client.post("http://127.0.0.1:8000/start-simulation", json=sim_payload)
            assert start_res.status_code == 200, f"Start simulation failed: {start_res.status_code}"
            sim_data = start_res.json()
            session_id = sim_data["session_id"]
            print(f" [PASS] Simulation Started successfully (session_id={session_id})")

        # 6. Receive live streamed risk updates over WebSocket
        print("Receiving live risk update chunks...")
        received_chunks = []
        for _ in range(4):
            msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
            update = json.loads(msg)
            received_chunks.append(update)
            print(f"   -> Chunk #{update.get('chunk_id')}: rolling_score={update.get('rolling_risk_score')} alert={update.get('alert_level')} advisory={update.get('advisory', {}).get('recommendation')}")
            
            # Verify 7-field contract
            for field in ["chunk_id", "timestamp", "chunk_score", "rolling_risk_score", "confidence", "flags", "alert_level"]:
                assert field in update, f"Missing contract field {field}"

        print(f" [PASS] Successfully received {len(received_chunks)} live WebSocket risk update chunks!")

        # 7. Stop Simulation
        async with httpx.AsyncClient() as client:
            stop_res = await client.post("http://127.0.0.1:8000/stop-simulation")
            assert stop_res.status_code == 200
            print(" [PASS] Simulation stopped successfully")

        # 8. Verify SQLite Session History Logging
        async with httpx.AsyncClient() as client:
            hist_res = await client.get(f"http://127.0.0.1:8000/sessions/{session_id}/history")
            assert hist_res.status_code == 200, f"History fetch failed: {hist_res.status_code}"
            hist_data = hist_res.json()
            assert hist_data["total_chunks"] >= 4
            print(f" [PASS] SQLite Session History retrieved: {hist_data['total_chunks']} chunks persisted for session {session_id}")

    print("=" * 60)
    print("ALL 8 LIVE INTEGRATION CHECKS PASSED PERFECTLY!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_live_e2e_tests())
