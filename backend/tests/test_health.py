def test_health_endpoint_returns_200(client):
    """Test health endpoint returns 200 OK."""
    response = client.get('/api/health')
    assert response.status_code == 200


def test_health_endpoint_returns_healthy_status(client):
    """Test health endpoint returns healthy status."""
    response = client.get('/api/health')
    data = response.get_json()
    assert data == {'status': 'healthy'}
