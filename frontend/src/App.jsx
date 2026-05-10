import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import TaskList from './pages/TaskList'
import TaskDetail from './pages/TaskDetail'
import TaskBuilder from './pages/TaskBuilder'
import AssetManager from './pages/AssetManager'
import UserProgress from './pages/UserProgress'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="tasks" element={<TaskList />} />
          <Route path="tasks/new" element={<TaskBuilder />} />
          <Route path="tasks/:id" element={<TaskDetail />} />
          <Route path="tasks/:id/edit" element={<TaskBuilder />} />
          <Route path="assets" element={<AssetManager />} />
          <Route path="users" element={<UserProgress />} />
          <Route path="users/:id" element={<UserProgress />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
