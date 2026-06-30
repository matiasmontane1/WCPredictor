import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from './api/client'
import { BottomNav } from './components/BottomNav'
import { Settings } from './pages/Settings'

const Dashboard = lazy(() => import('./pages/Dashboard').then((m) => ({ default: m.Dashboard })))
const MatchDetail = lazy(() => import('./pages/MatchDetail').then((m) => ({ default: m.MatchDetail })))
const Results = lazy(() => import('./pages/Results').then((m) => ({ default: m.Results })))
const Stats = lazy(() => import('./pages/Stats').then((m) => ({ default: m.Stats })))
const Admin = lazy(() => import('./pages/Admin').then((m) => ({ default: m.Admin })))

function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="animate-spin w-8 h-8 border-2 border-green-500 border-t-transparent rounded-full" />
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-slate-900">
          <Suspense fallback={<PageLoader />}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/match/:id" element={<MatchDetail />} />
              <Route path="/results" element={<Results />} />
              <Route path="/stats" element={<Stats />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/admin" element={<Admin />} />
            </Routes>
          </Suspense>
          <BottomNav />
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
