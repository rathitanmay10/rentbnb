async def test_get_amenities(client, create_sample_amenity, create_guest_user_token):
    amenity = create_sample_amenity
    response = await client.get(
        "/api/v1/amenities/",
        headers={"Authorization": f"Bearer {create_guest_user_token}"},
    )
    assert response.status_code == 200
    assert response.json()["data"][0]["name"] == amenity.name


async def test_create_amenity(client, create_admin_user_token):
    response = await client.post(
        "/api/v1/amenities/",
        headers={"Authorization": f"Bearer {create_admin_user_token}"},
        json={"name": "Test Amenity"},
    )
    assert response.status_code == 201
    assert response.json()["name"] == "test amenity"
