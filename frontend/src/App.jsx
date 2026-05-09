import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import TaskList from './pages/TaskList'
import TaskDetail from './pages/TaskDetail'
import TaskBuilder from './pages/TaskBuilder'

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
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
