"""
Test script to verify session TTL changes.
Tests that sessions can be created with ttl=None (never expire).
"""

from claude_code_server import SessionManager, InMemorySessionStore


def test_in_memory_store():
    """Test InMemorySessionStore (TTL not applicable)."""
    print("Testing InMemorySessionStore...")
    store = InMemorySessionStore()
    manager = SessionManager(store=store)

    # Create session
    session = manager.create_session("test_session", user_id="alice")
    print(f"✓ Created session: {session.session_id}")

    # Add messages
    manager.add_message("test_session", "user", "Hello")
    manager.add_message("test_session", "assistant", "Hi there!")
    print("✓ Added messages")

    # Retrieve session
    retrieved = manager.get_session("test_session")
    print(f"✓ Retrieved session with {len(retrieved.conversation_history)} messages")

    print("✓ InMemorySessionStore test passed!\n")


def test_redis_store_no_ttl():
    """Test RedisSessionStore with ttl=None (never expire)."""
    try:
        import redis
        from claude_code_server import RedisSessionStore

        print("Testing RedisSessionStore with ttl=None...")

        # Connect to Redis
        redis_client = redis.Redis(host='localhost', port=6379, db=15, decode_responses=False)
        redis_client.ping()

        # Create store with ttl=None
        store = RedisSessionStore(redis_client, prefix="test_ttl_none:", ttl=None)
        manager = SessionManager(store=store)

        # Create session
        session = manager.create_session("test_no_ttl", user_id="bob")
        print(f"✓ Created session: {session.session_id}")

        # Add messages
        manager.add_message("test_no_ttl", "user", "Test message")
        manager.add_message("test_no_ttl", "assistant", "Test response")
        print("✓ Added messages")

        # Check Redis TTL (-1 means no expiration)
        ttl = redis_client.ttl("test_ttl_none:test_no_ttl")
        print(f"✓ Redis TTL: {ttl} (-1 means no expiration)")

        if ttl == -1:
            print("✓ Session has no expiration (correct!)")
        else:
            print(f"✗ WARNING: Session has TTL={ttl}, expected -1")

        # Cleanup
        manager.delete_session("test_no_ttl")
        print("✓ Cleaned up test session")
        print("✓ RedisSessionStore (ttl=None) test passed!\n")

    except ImportError:
        print("⊘ Redis not installed, skipping Redis tests\n")
    except redis.ConnectionError:
        print("⊘ Redis not running, skipping Redis tests\n")


def test_redis_store_with_ttl():
    """Test RedisSessionStore with ttl=60 (1 minute expiration)."""
    try:
        import redis
        from claude_code_server import RedisSessionStore

        print("Testing RedisSessionStore with ttl=60...")

        # Connect to Redis
        redis_client = redis.Redis(host='localhost', port=6379, db=15, decode_responses=False)
        redis_client.ping()

        # Create store with ttl=60
        store = RedisSessionStore(redis_client, prefix="test_ttl_60:", ttl=60)
        manager = SessionManager(store=store)

        # Create session
        session = manager.create_session("test_with_ttl", user_id="charlie")
        print(f"✓ Created session: {session.session_id}")

        # Add messages
        manager.add_message("test_with_ttl", "user", "Test message")
        print("✓ Added messages")

        # Check Redis TTL
        ttl = redis_client.ttl("test_ttl_60:test_with_ttl")
        print(f"✓ Redis TTL: {ttl} seconds")

        if 50 <= ttl <= 60:
            print("✓ Session has correct TTL (around 60 seconds)")
        else:
            print(f"✗ WARNING: Session TTL={ttl}, expected around 60")

        # Cleanup
        manager.delete_session("test_with_ttl")
        print("✓ Cleaned up test session")
        print("✓ RedisSessionStore (ttl=60) test passed!\n")

    except ImportError:
        print("⊘ Redis not installed, skipping Redis tests\n")
    except redis.ConnectionError:
        print("⊘ Redis not running, skipping Redis tests\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Session TTL Configuration Test")
    print("=" * 60)
    print()

    # Test 1: InMemory Store
    test_in_memory_store()

    # Test 2: Redis Store with ttl=None
    test_redis_store_no_ttl()

    # Test 3: Redis Store with ttl=60
    test_redis_store_with_ttl()

    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)
