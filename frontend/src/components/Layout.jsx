import React, { useState } from 'react'
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import {
  HomeIcon,
  DocumentTextIcon,
  ClipboardDocumentListIcon,
  VideoCameraIcon,
  UserIcon,
  Bars3Icon,
  XMarkIcon,
  ArrowRightOnRectangleIcon,
  PlusIcon,
  AcademicCapIcon
} from '@heroicons/react/24/outline'
import clsx from 'clsx'

const Layout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { user, logout, isTeacher, isStudent } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  // Navigation items based on user role
  const getNavigationItems = () => {
    const commonItems = [
      {
        name: 'Dashboard',
        href: isTeacher ? '/teacher/dashboard' : '/student/dashboard',
        icon: HomeIcon,
      },
      {
        name: 'Assignments',
        href: '/assignments',
        icon: DocumentTextIcon,
      },
      {
        name: 'Submissions',
        href: '/submissions',
        icon: ClipboardDocumentListIcon,
      },
      {
        name: 'Viva Sessions',
        href: '/viva',
        icon: VideoCameraIcon,
      },
    ]

    if (isTeacher) {
      return [
        ...commonItems,
        {
          name: 'Create Assignment',
          href: '/assignments/create',
          icon: PlusIcon,
        },
      ]
    }

    return commonItems
  }

  const navigation = getNavigationItems()

  const isCurrentPath = (path) => {
    return location.pathname === path || location.pathname.startsWith(path + '/')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar */}
      <div className={clsx(
        'fixed inset-0 z-40 lg:hidden',
        sidebarOpen ? 'block' : 'hidden'
      )}>
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)} />
        <div className="relative flex w-full max-w-xs flex-1 flex-col bg-white">
          <div className="absolute top-0 right-0 -mr-12 pt-2">
            <button
              type="button"
              className="ml-1 flex h-10 w-10 items-center justify-center rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
              onClick={() => setSidebarOpen(false)}
            >
              <XMarkIcon className="h-6 w-6 text-white" />
            </button>
          </div>
          <SidebarContent navigation={navigation} isCurrentPath={isCurrentPath} user={user} onLogout={handleLogout} />
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex min-h-0 flex-1 flex-col bg-white border-r border-gray-200">
          <SidebarContent navigation={navigation} isCurrentPath={isCurrentPath} user={user} onLogout={handleLogout} />
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <div className="sticky top-0 z-10 bg-white border-b border-gray-200 lg:hidden">
          <div className="flex h-16 items-center justify-between px-4">
            <button
              type="button"
              className="text-gray-500 hover:text-gray-600"
              onClick={() => setSidebarOpen(true)}
            >
              <Bars3Icon className="h-6 w-6" />
            </button>
            <div className="flex items-center space-x-4">
              <span className="text-sm font-medium text-gray-900">{user?.full_name}</span>
              <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center">
                <span className="text-sm font-medium text-primary-600">
                  {user?.full_name?.charAt(0)?.toUpperCase()}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

const SidebarContent = ({ navigation, isCurrentPath, user, onLogout }) => {
  return (
    <>
      {/* Logo */}
      <div className="flex flex-shrink-0 items-center px-4 py-4">
        <div className="flex items-center">
          <AcademicCapIcon className="h-8 w-8 text-primary-600" />
          <div className="ml-3">
            <h1 className="text-lg font-semibold text-gray-900">Viva Platform</h1>
            <p className="text-xs text-gray-500">AI-Powered Assessment</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-2 pb-4">
        {navigation.map((item) => (
          <Link
            key={item.name}
            to={item.href}
            className={clsx(
              'group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors',
              isCurrentPath(item.href)
                ? 'bg-primary-100 text-primary-900'
                : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
            )}
          >
            <item.icon
              className={clsx(
                'mr-3 h-5 w-5 flex-shrink-0',
                isCurrentPath(item.href)
                  ? 'text-primary-500'
                  : 'text-gray-400 group-hover:text-gray-500'
              )}
            />
            {item.name}
          </Link>
        ))}
      </nav>

      {/* User section */}
      <div className="flex-shrink-0 border-t border-gray-200 p-4">
        <div className="flex items-center">
          <div className="h-10 w-10 rounded-full bg-primary-100 flex items-center justify-center">
            <span className="text-sm font-medium text-primary-600">
              {user?.full_name?.charAt(0)?.toUpperCase()}
            </span>
          </div>
          <div className="ml-3 flex-1">
            <p className="text-sm font-medium text-gray-900">{user?.full_name}</p>
            <p className="text-xs text-gray-500 capitalize">{user?.role}</p>
          </div>
        </div>
        <div className="mt-3 space-y-1">
          <Link
            to="/profile"
            className="group flex items-center px-2 py-2 text-sm font-medium text-gray-600 rounded-md hover:bg-gray-50 hover:text-gray-900"
          >
            <UserIcon className="mr-3 h-4 w-4 text-gray-400 group-hover:text-gray-500" />
            Profile
          </Link>
          <button
            onClick={onLogout}
            className="group flex w-full items-center px-2 py-2 text-sm font-medium text-gray-600 rounded-md hover:bg-gray-50 hover:text-gray-900"
          >
            <ArrowRightOnRectangleIcon className="mr-3 h-4 w-4 text-gray-400 group-hover:text-gray-500" />
            Sign out
          </button>
        </div>
      </div>
    </>
  )
}

export default Layout
