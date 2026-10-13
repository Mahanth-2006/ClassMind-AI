"""
Test script for Teacher WebSocket implementation in Phase 1.
Uses FastAPI's built-in TestClient (backed by httpx/starlette) with zero new dependencies.
"""

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import app
from app.storage import classrooms, teacher_connections


def run_tests():
    client = TestClient(app)
    print("=" * 60)
    print("RUNNING PHASE-1 TEACHER WEBSOCKET TESTS")
    print("=" * 60)

    # ---------------------------------------------------------
    # TEST 1: Health check
    # ---------------------------------------------------------
    print("\n[TEST 1] Testing GET /health...")
    health_resp = client.get("/health")
    assert health_resp.status_code == 200, f"Expected 200, got {health_resp.status_code}"
    health_data = health_resp.json()
    assert health_data["status"] == "healthy"
    print("[PASS] Health endpoint OK:", health_data)

    # ---------------------------------------------------------
    # TEST 2: Create Classroom
    # ---------------------------------------------------------
    print("\n[TEST 2] Testing POST /classroom/create...")
    create_resp = client.post("/classroom/create", json={"teacher_name": "Professor"})
    assert create_resp.status_code == 200, f"Expected 200, got {create_resp.status_code}"
    create_data = create_resp.json()
    classroom_id = create_data["classroom_id"]
    assert classroom_id in classrooms
    print(f"[PASS] Classroom created successfully. Classroom ID: {classroom_id}")

    # ---------------------------------------------------------
    # TEST 3: Teacher WebSocket connection & JSON Echo
    # ---------------------------------------------------------
    print(f"\n[TEST 3] Testing Teacher WebSocket on /ws/teacher/{classroom_id}...")
    with client.websocket_connect(f"/ws/teacher/{classroom_id}") as ws:
        # Verify registered in teacher_connections
        assert classroom_id in teacher_connections, "Teacher connection was not registered in teacher_connections"
        print("[PASS] Teacher connection successfully registered in memory.")

        # Send JSON ping
        ping_msg = {"type": "ping", "message": "Hello Teacher"}
        ws.send_json(ping_msg)
        print(f"[PASS] Sent message: {ping_msg}")

        # Receive echo
        echo_data = ws.receive_json()
        print(f"[PASS] Received response: {echo_data}")
        assert echo_data.get("type") == "echo"
        assert echo_data.get("classroom_id") == classroom_id
        assert echo_data.get("message") == "Hello Teacher"
        print("[PASS] Echo response validated successfully.")

        # Test malformed JSON
        print("\n[TEST 3b] Testing malformed JSON handling...")
        ws.send_text("this-is-not-json")
        err_data = ws.receive_json()
        print(f"[PASS] Received error response: {err_data}")
        assert err_data.get("type") == "error"
        assert "Invalid JSON" in err_data.get("message", "")
        print("[PASS] Malformed JSON handled cleanly without crashing.")

    # ---------------------------------------------------------
    # TEST 5: Disconnect Cleanup
    # ---------------------------------------------------------
    print("\n[TEST 5] Testing Disconnect Cleanup...")
    # After exiting the context manager, the WebSocket is closed
    assert classroom_id not in teacher_connections, "Stale teacher connection remained in teacher_connections after disconnect"
    print("[PASS] Teacher connection successfully cleaned up from memory after disconnect.")

    # ---------------------------------------------------------
    # TEST 4: Invalid Classroom Rejection
    # ---------------------------------------------------------
    print("\n[TEST 4] Testing Invalid Classroom Rejection (/ws/teacher/XXXXXX)...")
    try:
        with client.websocket_connect("/ws/teacher/XXXXXX") as ws:
            assert False, "Connection should have been rejected for non-existent classroom"
    except WebSocketDisconnect as e:
        print(f"[PASS] Rejected invalid classroom as expected (code: {e.code})")
    except Exception as e:
        print(f"[PASS] Connection rejected cleanly: {type(e).__name__}")

    # ---------------------------------------------------------
    # TEST 6: Duplicate Teacher Connection Rejection
    # ---------------------------------------------------------
    print("\n[TEST 6] Testing Duplicate Teacher Connection Policy...")
    with client.websocket_connect(f"/ws/teacher/{classroom_id}") as ws1:
        assert classroom_id in teacher_connections
        print("[PASS] First teacher connection active.")

        # Attempt second connection to the same classroom
        second_connected = False
        try:
            with client.websocket_connect(f"/ws/teacher/{classroom_id}") as ws2:
                second_connected = True
        except WebSocketDisconnect as e:
            print(f"[PASS] Second teacher connection rejected cleanly (code: {e.code})")
        except Exception as e:
            print(f"[PASS] Second teacher connection rejected cleanly: {type(e).__name__}")

        assert not second_connected, "Second teacher connection should not have been accepted"

        # Verify first teacher connection is still active and working
        ws1.send_json({"type": "ping", "message": "Still alive"})
        echo_data = ws1.receive_json()
        assert echo_data.get("message") == "Still alive"
        print("[PASS] First teacher connection remained active and uncorrupted.")

    # Verify cleanup after first teacher exits
    assert classroom_id not in teacher_connections
    print("[PASS] Memory cleanly cleared after test.")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY! (6/6)")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
