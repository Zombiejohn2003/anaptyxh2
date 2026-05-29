import { useEffect, useMemo, useState } from 'react'
import { Activity, Edit, LogOut, Plus, Trash2 } from 'lucide-react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  currentUser,
  deleteSensor,
  deleteUser,
  getCategories,
  getDashboard,
  getSensor,
  getSensorMeasurements,
  login,
  saveSensor,
  saveUser,
  setAuthToken,
} from './api'

const COLORS = ['#2563eb', '#16a34a', '#f97316', '#dc2626', '#7c3aed']
const emptySensor = {
  identifier: '',
  name: '',
  description: '',
  location: '',
  status: 'active',
  category_ids: [],
}
const emptyUser = {
  username: '',
  password: '',
  full_name: '',
  email: '',
  role: 'user',
  is_active: true,
}

function formatDate(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString()
}

function App() {
  const [token, setToken] = useState(() => localStorage.getItem('sensorToken'))
  const [user, setUser] = useState(null)
  const [booting, setBooting] = useState(Boolean(token))
  const [authError, setAuthError] = useState('')

  useEffect(() => {
    if (!token) {
      setBooting(false)
      return
    }
    setAuthToken(token)
    currentUser()
      .then(setUser)
      .catch(() => {
        localStorage.removeItem('sensorToken')
        setAuthToken(null)
        setToken(null)
      })
      .finally(() => setBooting(false))
  }, [token])

  async function handleLogin(credentials) {
    setAuthError('')
    try {
      const data = await login(credentials)
      localStorage.setItem('sensorToken', data.access_token)
      setAuthToken(data.access_token)
      setToken(data.access_token)
      setUser(data.user)
    } catch (error) {
      setAuthError(error.response?.data?.message || 'Login failed')
    }
  }

  function handleLogout() {
    localStorage.removeItem('sensorToken')
    setAuthToken(null)
    setToken(null)
    setUser(null)
  }

  if (booting) return <div className="centered">Loading application...</div>
  if (!user) return <LoginPage error={authError} onLogin={handleLogin} />

  return <Dashboard user={user} onLogout={handleLogout} />
}

function LoginPage({ error, onLogin }) {
  const [credentials, setCredentials] = useState({ username: 'admin', password: 'admin123' })

  function submit(event) {
    event.preventDefault()
    onLogin(credentials)
  }

  return (
    <main className="login-shell">
      <form className="login-card" onSubmit={submit}>
        <Activity size={44} />
        <h1>Sensor Dashboard</h1>
        <p>Sign in to access sensor monitoring data.</p>
        <label>
          Username
          <input
            value={credentials.username}
            onChange={(event) => setCredentials({ ...credentials, username: event.target.value })}
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            value={credentials.password}
            onChange={(event) => setCredentials({ ...credentials, password: event.target.value })}
            required
          />
        </label>
        {error && <div className="error">{error}</div>}
        <button type="submit">Login</button>
        <small>Demo accounts: admin/admin123 and user/user123</small>
      </form>
    </main>
  )
}

function Dashboard({ user, onLogout }) {
  const [dashboard, setDashboard] = useState(null)
  const [categories, setCategories] = useState([])
  const [selectedSensorId, setSelectedSensorId] = useState(null)
  const [editingSensor, setEditingSensor] = useState(null)
  const [editingUser, setEditingUser] = useState(null)
  const [notice, setNotice] = useState('')
  const isAdmin = user.role === 'admin'

  async function refresh() {
    const [dashboardData, categoryData] = await Promise.all([getDashboard(), getCategories()])
    setDashboard(dashboardData)
    setCategories(categoryData)
  }

  useEffect(() => {
    refresh().catch((error) => setNotice(error.response?.data?.message || 'Could not load dashboard data'))
  }, [])

  if (!dashboard) return <div className="centered">Loading dashboard...</div>

  if (selectedSensorId) {
    return (
      <SensorDetail
        sensorId={selectedSensorId}
        onBack={() => setSelectedSensorId(null)}
        onLogout={onLogout}
        user={user}
      />
    )
  }

  async function handleSensorSave(sensor) {
    await saveSensor(sensor)
    setEditingSensor(null)
    setNotice('Sensor saved successfully.')
    await refresh()
  }

  async function handleSensorDelete(sensorId) {
    await deleteSensor(sensorId)
    setNotice('Sensor deleted successfully.')
    await refresh()
  }

  async function handleUserSave(account) {
    await saveUser(account)
    setEditingUser(null)
    setNotice('User saved successfully.')
    await refresh()
  }

  async function handleUserDelete(userId) {
    await deleteUser(userId)
    setNotice('User deleted successfully.')
    await refresh()
  }

  return (
    <main className="app-shell">
      <Header user={user} onLogout={onLogout} />
      {notice && <div className="notice">{notice}</div>}

      <section className="summary-grid">
        <SummaryCard title="Total sensors" value={dashboard.summary.total_sensors} />
        <SummaryCard title="Active sensors" value={dashboard.summary.active_sensors} />
        <SummaryCard title="Average temperature" value={dashboard.summary.average_temperature ?? '-'} suffix=" C" />
        <SummaryCard title="Average humidity" value={dashboard.summary.average_humidity ?? '-'} suffix=" %" />
      </section>

      <section className="chart-grid">
        <Panel title="Sensor categories">
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie dataKey="value" nameKey="name" data={dashboard.sensor_type_distribution} outerRadius={90} label>
                {dashboard.sensor_type_distribution.map((entry, index) => (
                  <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </Panel>
        <Panel title="Sensor status">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={dashboard.sensor_status_distribution}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="value" fill="#2563eb" />
            </BarChart>
          </ResponsiveContainer>
        </Panel>
      </section>

      <Panel
        title="Available sensors"
        action={
          isAdmin && (
            <button className="secondary" onClick={() => setEditingSensor({ ...emptySensor })}>
              <Plus size={16} /> Add sensor
            </button>
          )
        }
      >
        <SensorTable
          sensors={dashboard.sensors}
          isAdmin={isAdmin}
          onOpen={setSelectedSensorId}
          onEdit={(sensor) =>
            setEditingSensor({
              ...sensor,
              category_ids: sensor.categories.map((category) => category.id),
            })
          }
          onDelete={handleSensorDelete}
        />
      </Panel>

      {editingSensor && (
        <Panel title={editingSensor.id ? 'Edit sensor' : 'Create sensor'}>
          <SensorForm
            sensor={editingSensor}
            categories={categories}
            onCancel={() => setEditingSensor(null)}
            onSave={handleSensorSave}
          />
        </Panel>
      )}

      {isAdmin && (
        <Panel
          title="Active users"
          action={
            <button className="secondary" onClick={() => setEditingUser({ ...emptyUser })}>
              <Plus size={16} /> Add user
            </button>
          }
        >
          <UserTable users={dashboard.users || []} onEdit={setEditingUser} onDelete={handleUserDelete} />
        </Panel>
      )}

      {isAdmin && editingUser && (
        <Panel title={editingUser.id ? 'Edit user' : 'Create user'}>
          <UserForm user={editingUser} onCancel={() => setEditingUser(null)} onSave={handleUserSave} />
        </Panel>
      )}
    </main>
  )
}

function Header({ user, onLogout }) {
  return (
    <header className="topbar">
      <div>
        <h1>Sensor Monitoring Dashboard</h1>
        <p>Signed in as {user.full_name} ({user.role})</p>
      </div>
      <button className="ghost" onClick={onLogout}>
        <LogOut size={18} /> Logout
      </button>
    </header>
  )
}

function SummaryCard({ title, value, suffix = '' }) {
  return (
    <article className="summary-card">
      <span>{title}</span>
      <strong>{value}{suffix}</strong>
    </article>
  )
}

function Panel({ title, action, children }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>{title}</h2>
        {action}
      </div>
      {children}
    </section>
  )
}

function SensorTable({ sensors, isAdmin, onOpen, onEdit, onDelete }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Identifier</th>
            <th>Name</th>
            <th>Location</th>
            <th>Status</th>
            <th>Categories</th>
            {isAdmin && <th>Actions</th>}
          </tr>
        </thead>
        <tbody>
          {sensors.map((sensor) => (
            <tr key={sensor.id}>
              <td><button className="link" onClick={() => onOpen(sensor.id)}>{sensor.identifier}</button></td>
              <td>{sensor.name}</td>
              <td>{sensor.location}</td>
              <td><span className={`status ${sensor.status}`}>{sensor.status}</span></td>
              <td>{sensor.categories.map((category) => category.name).join(', ')}</td>
              {isAdmin && (
                <td className="actions">
                  <button className="icon" onClick={() => onEdit(sensor)}><Edit size={16} /></button>
                  <button className="icon danger" onClick={() => onDelete(sensor.id)}><Trash2 size={16} /></button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function SensorForm({ sensor, categories, onCancel, onSave }) {
  const [form, setForm] = useState(sensor)
  const [error, setError] = useState('')

  function toggleCategory(categoryId) {
    const categoryIds = form.category_ids.includes(categoryId)
      ? form.category_ids.filter((id) => id !== categoryId)
      : [...form.category_ids, categoryId]
    setForm({ ...form, category_ids: categoryIds })
  }

  async function submit(event) {
    event.preventDefault()
    setError('')
    if (form.category_ids.length === 0) {
      setError('Select at least one category.')
      return
    }
    try {
      await onSave(form)
    } catch (apiError) {
      setError(apiError.response?.data?.message || 'Could not save sensor')
    }
  }

  return (
    <form className="form-grid" onSubmit={submit}>
      <label>Identifier<input value={form.identifier} onChange={(event) => setForm({ ...form, identifier: event.target.value })} required /></label>
      <label>Name<input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required /></label>
      <label>Location<input value={form.location} onChange={(event) => setForm({ ...form, location: event.target.value })} /></label>
      <label>Status
        <select value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })}>
          <option value="active">active</option>
          <option value="maintenance">maintenance</option>
          <option value="inactive">inactive</option>
        </select>
      </label>
      <label className="wide">Description<textarea value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} /></label>
      <fieldset className="wide">
        <legend>Measurement categories</legend>
        {categories.map((category) => (
          <label className="checkbox" key={category.id}>
            <input type="checkbox" checked={form.category_ids.includes(category.id)} onChange={() => toggleCategory(category.id)} />
            {category.name} ({category.unit})
          </label>
        ))}
      </fieldset>
      {error && <div className="error wide">{error}</div>}
      <div className="form-actions wide">
        <button type="button" className="ghost" onClick={onCancel}>Cancel</button>
        <button type="submit">Save sensor</button>
      </div>
    </form>
  )
}

function UserTable({ users, onEdit, onDelete }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr><th>Username</th><th>Full name</th><th>Email</th><th>Role</th><th>Active</th><th>Actions</th></tr>
        </thead>
        <tbody>
          {users.map((account) => (
            <tr key={account.id}>
              <td>{account.username}</td>
              <td>{account.full_name}</td>
              <td>{account.email}</td>
              <td>{account.role}</td>
              <td>{account.is_active ? 'yes' : 'no'}</td>
              <td className="actions">
                <button className="icon" onClick={() => onEdit({ ...account, password: '' })}><Edit size={16} /></button>
                <button className="icon danger" onClick={() => onDelete(account.id)}><Trash2 size={16} /></button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function UserForm({ user, onCancel, onSave }) {
  const [form, setForm] = useState(user)
  const [error, setError] = useState('')

  async function submit(event) {
    event.preventDefault()
    setError('')
    try {
      await onSave(form)
    } catch (apiError) {
      setError(apiError.response?.data?.message || 'Could not save user')
    }
  }

  return (
    <form className="form-grid" onSubmit={submit}>
      <label>Username<input value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })} required /></label>
      <label>Password<input type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} required={!form.id} /></label>
      <label>Full name<input value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} required /></label>
      <label>Email<input type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} required /></label>
      <label>Role
        <select value={form.role} onChange={(event) => setForm({ ...form, role: event.target.value })}>
          <option value="user">Simple user</option>
          <option value="admin">Administrator</option>
        </select>
      </label>
      <label className="checkbox"><input type="checkbox" checked={form.is_active} onChange={(event) => setForm({ ...form, is_active: event.target.checked })} /> Active account</label>
      {error && <div className="error wide">{error}</div>}
      <div className="form-actions wide">
        <button type="button" className="ghost" onClick={onCancel}>Cancel</button>
        <button type="submit">Save user</button>
      </div>
    </form>
  )
}

function SensorDetail({ sensorId, user, onBack, onLogout }) {
  const [sensor, setSensor] = useState(null)
  const [resolution, setResolution] = useState('hour')
  const [measurements, setMeasurements] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    getSensor(sensorId).then(setSensor).catch(() => setError('Could not load sensor'))
  }, [sensorId])

  useEffect(() => {
    getSensorMeasurements(sensorId, resolution)
      .then(setMeasurements)
      .catch(() => setError('Could not load measurements'))
  }, [sensorId, resolution])

  const chartData = useMemo(() => {
    const grouped = new Map()
    measurements.forEach((row) => {
      const label = new Date(row.period).toLocaleString()
      const item = grouped.get(label) || { period: label }
      item[row.category] = row.average
      grouped.set(label, item)
    })
    return Array.from(grouped.values())
  }, [measurements])

  if (error) return <div className="centered error">{error}</div>
  if (!sensor) return <div className="centered">Loading sensor...</div>

  return (
    <main className="app-shell">
      <Header user={user} onLogout={onLogout} />
      <button className="ghost back" onClick={onBack}>Back to dashboard</button>
      <Panel title={sensor.name}>
        <div className="metadata-grid">
          <div><span>Identifier</span><strong>{sensor.identifier}</strong></div>
          <div><span>Status</span><strong>{sensor.status}</strong></div>
          <div><span>Location</span><strong>{sensor.location || '-'}</strong></div>
          <div><span>Created</span><strong>{formatDate(sensor.created_at)}</strong></div>
          <div className="wide"><span>Description</span><strong>{sensor.description || '-'}</strong></div>
          <div className="wide"><span>Categories</span><strong>{sensor.categories.map((category) => `${category.name} (${category.unit})`).join(', ')}</strong></div>
        </div>
      </Panel>
      <Panel
        title="Measurement history"
        action={
          <label className="inline-select">Resolution
            <select value={resolution} onChange={(event) => setResolution(event.target.value)}>
              <option value="hour">Hour</option>
              <option value="day">Day</option>
              <option value="month">Month</option>
            </select>
          </label>
        }
      >
        <ResponsiveContainer width="100%" height={360}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="period" minTickGap={24} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="temperature" stroke="#dc2626" strokeWidth={2} connectNulls />
            <Line type="monotone" dataKey="humidity" stroke="#2563eb" strokeWidth={2} connectNulls />
          </LineChart>
        </ResponsiveContainer>
      </Panel>
    </main>
  )
}

export default App
