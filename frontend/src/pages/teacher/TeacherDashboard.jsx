import React from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from 'react-query'
import { usersAPI, assignmentsAPI, submissionsAPI } from '../../services/api'
import { useAuth } from '../../contexts/AuthContext'
import LoadingSpinner from '../../components/LoadingSpinner'
import {
  PlusIcon,
  DocumentTextIcon,
  ClipboardDocumentListIcon,
  VideoCameraIcon,
  UserGroupIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'

const TeacherDashboard = () => {
  const { user } = useAuth()

  // Fetch dashboard stats
  const { data: stats, isLoading: statsLoading } = useQuery(
    'dashboard-stats',
    usersAPI.getDashboardStats,
    {
      refetchOnWindowFocus: false,
    }
  )

  // Fetch recent assignments
  const { data: assignments, isLoading: assignmentsLoading } = useQuery(
    'recent-assignments',
    () => assignmentsAPI.list({ limit: 5 }),
    {
      refetchOnWindowFocus: false,
    }
  )

  // Fetch recent submissions
  const { data: submissions, isLoading: submissionsLoading } = useQuery(
    'recent-submissions',
    () => submissionsAPI.list({ limit: 5 }),
    {
      refetchOnWindowFocus: false,
    }
  )

  if (statsLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" text="Loading dashboard..." />
      </div>
    )
  }

  const quickActions = [
    {
      name: 'Create Assignment',
      description: 'Create a new assignment with viva questions',
      href: '/assignments/create',
      icon: PlusIcon,
      color: 'bg-primary-500 hover:bg-primary-600',
    },
    {
      name: 'View Assignments',
      description: 'Manage your existing assignments',
      href: '/assignments',
      icon: DocumentTextIcon,
      color: 'bg-secondary-500 hover:bg-secondary-600',
    },
    {
      name: 'Review Submissions',
      description: 'Review student submissions and viva sessions',
      href: '/submissions',
      icon: ClipboardDocumentListIcon,
      color: 'bg-success-500 hover:bg-success-600',
    },
    {
      name: 'Viva Sessions',
      description: 'Monitor ongoing and completed viva sessions',
      href: '/viva',
      icon: VideoCameraIcon,
      color: 'bg-warning-500 hover:bg-warning-600',
    },
  ]

  const statCards = [
    {
      name: 'Total Assignments',
      value: stats?.total_assignments || 0,
      icon: DocumentTextIcon,
      color: 'text-primary-600 bg-primary-100',
    },
    {
      name: 'Active Assignments',
      value: stats?.active_assignments || 0,
      icon: ChartBarIcon,
      color: 'text-success-600 bg-success-100',
    },
    {
      name: 'Total Submissions',
      value: stats?.total_submissions || 0,
      icon: ClipboardDocumentListIcon,
      color: 'text-secondary-600 bg-secondary-100',
    },
    {
      name: 'Pending Reviews',
      value: stats?.pending_reviews || 0,
      icon: UserGroupIcon,
      color: 'text-warning-600 bg-warning-100',
    },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome back, {user?.full_name}!
          </h1>
          <p className="mt-2 text-gray-600">
            Here's what's happening with your assignments and students today.
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {statCards.map((stat) => (
            <div key={stat.name} className="card">
              <div className="card-body">
                <div className="flex items-center">
                  <div className={`p-2 rounded-lg ${stat.color}`}>
                    <stat.icon className="h-6 w-6" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                    <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {quickActions.map((action) => (
              <Link
                key={action.name}
                to={action.href}
                className={`${action.color} text-white p-6 rounded-lg shadow-sm hover:shadow-md transition-all duration-200 group`}
              >
                <div className="flex items-center">
                  <action.icon className="h-8 w-8 mb-2" />
                </div>
                <h3 className="text-lg font-semibold mb-1">{action.name}</h3>
                <p className="text-sm opacity-90">{action.description}</p>
              </Link>
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Recent Assignments */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-medium text-gray-900">Recent Assignments</h3>
              <Link
                to="/assignments"
                className="text-sm text-primary-600 hover:text-primary-500"
              >
                View all
              </Link>
            </div>
            <div className="card-body">
              {assignmentsLoading ? (
                <LoadingSpinner />
              ) : assignments?.data?.length > 0 ? (
                <div className="space-y-4">
                  {assignments.data.slice(0, 5).map((assignment) => (
                    <div key={assignment.id} className="flex items-center justify-between">
                      <div>
                        <h4 className="text-sm font-medium text-gray-900">
                          {assignment.title}
                        </h4>
                        <p className="text-sm text-gray-500">
                          {assignment.question_count} questions • {assignment.viva_question_count} viva questions
                        </p>
                      </div>
                      <span className={`badge ${assignment.is_active ? 'badge-success' : 'badge-secondary'}`}>
                        {assignment.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-4">
                  No assignments yet. <Link to="/assignments/create" className="text-primary-600">Create your first assignment</Link>
                </p>
              )}
            </div>
          </div>

          {/* Recent Submissions */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-medium text-gray-900">Recent Submissions</h3>
              <Link
                to="/submissions"
                className="text-sm text-primary-600 hover:text-primary-500"
              >
                View all
              </Link>
            </div>
            <div className="card-body">
              {submissionsLoading ? (
                <LoadingSpinner />
              ) : submissions?.data?.length > 0 ? (
                <div className="space-y-4">
                  {submissions.data.slice(0, 5).map((submission) => (
                    <div key={submission.id} className="flex items-center justify-between">
                      <div>
                        <h4 className="text-sm font-medium text-gray-900">
                          {submission.assignment_title}
                        </h4>
                        <p className="text-sm text-gray-500">
                          by {submission.student_name}
                        </p>
                      </div>
                      <span className={`badge ${
                        submission.status === 'submitted' ? 'badge-warning' :
                        submission.status === 'graded' ? 'badge-success' :
                        'badge-secondary'
                      }`}>
                        {submission.status}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-4">
                  No submissions yet.
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default TeacherDashboard
