import axios from 'axios'

// Central Axios client: all React API calls use the same base URL and auth header.
const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:5000/api',
})

// After login/logout we update the Authorization header used by protected Flask routes.
export function setAuthToken(token) {
  if (token) {
    client.defaults.headers.common.Authorization = `Bearer ${token}`
  } else {
    delete client.defaults.headers.common.Authorization
  }
}

export async function login(credentials) {
  const { data } = await client.post('/auth/login', credentials)
  return data
}

export async function currentUser() {
  const { data } = await client.get('/auth/me')
  return data.user
}

export async function getDashboard() {
  const { data } = await client.get('/dashboard')
  return data
}

export async function getCategories() {
  const { data } = await client.get('/categories')
  return data.categories
}

export async function getSensor(sensorId) {
  const { data } = await client.get(`/sensors/${sensorId}`)
  return data.sensor
}

// The resolution parameter controls server-side grouping: hour, day, or month.
export async function getSensorMeasurements(sensorId, resolution) {
  const { data } = await client.get(`/sensors/${sensorId}/measurements`, { params: { resolution } })
  return data.measurements
}

export async function saveSensor(sensor) {
  const payload = {
    identifier: sensor.identifier,
    name: sensor.name,
    description: sensor.description,
    location: sensor.location,
    status: sensor.status,
    category_ids: sensor.category_ids,
  }
  if (sensor.id) {
    const { data } = await client.put(`/sensors/${sensor.id}`, payload)
    return data.sensor
  }
  const { data } = await client.post('/sensors', payload)
  return data.sensor
}

export async function deleteSensor(sensorId) {
  await client.delete(`/sensors/${sensorId}`)
}

export async function saveUser(user) {
  const payload = {
    username: user.username,
    full_name: user.full_name,
    email: user.email,
    role: user.role,
    is_active: user.is_active,
  }
  if (user.password) {
    payload.password = user.password
  }
  if (user.id) {
    const { data } = await client.put(`/users/${user.id}`, payload)
    return data.user
  }
  const { data } = await client.post('/users', payload)
  return data.user
}

export async function deleteUser(userId) {
  await client.delete(`/users/${userId}`)
}
