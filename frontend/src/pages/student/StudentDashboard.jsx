import React from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from 'react-query'
import { usersAPI, assignmentsAPI, submissionsAPI, vivaAPI } from '../../services/api'
import { useAuth } from '../../contexts/AuthContext'
import LoadingSpinner from '../../components/LoadingSpinner'
import {
  DocumentTextIcon,
  ClipboardDocumentListIcon,
  VideoCameraIcon,
  PlayIcon,
  ChartBarIcon,
  TrophyIcon
} from '@heroicons/react/24/outline'

const StudentDashboard = () => {
  const { user } = useAuth()

  // Fetch dashboard stats
  const { data: stats, isLoading: statsLoading } = useQuery(
    'dashboard-stats',
    usersAPI.getDashboardStats,
    {
      refetchOnWindowFocus: false,
    }
  )

  // Fetch available assignments
  const { data: assignments, isLoading: assignmentsLoading } = useQuery(
    'available-assignments',
    () => assignmentsAPI.list({ limit: 5 }),
    {
      refetchOnWindowFocus: false,
    }
  )

  // Fetch recent submissions
  const { data: submissions, isLoading: submissionsLoading } = useQuery(
    'my-submissions',
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

  const statCards = [
    {
      name: 'Total Submissions',
      value: stats?.total_submissions || 0,
      icon: ClipboardDocumentListIcon,
      color: 'text-primary-600 bg-primary-100',
    },
    {
      name: 'Completed Submissions',
      value: stats?.completed_submissions || 0,
      icon: DocumentTextIcon,
      color: 'text-success-600 bg-success-100',
    },
    {
      name: 'Completed Vivas',
      value: stats?.completed_vivas || 0,
      icon: VideoCameraIcon,
      color: 'text-secondary-600 bg-secondary-100',
    },
    {
      name: 'Average Score',
      value: stats?.average_score ? `${stats.average_score}%` : 'N/A',
      icon: TrophyIcon,
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
            Track your progress and continue your learning journey.
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

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Available Assignments */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-medium text-gray-900">Available Assignments</h3>
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
                    <div key={assignment.id} className="border border-gray-200 rounded-lg p-4 hover:border-primary-300 transition-colors">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-sm font-medium text-gray-900">
                          {assignment.title}
                        </h4>
                        <span className={`badge ${assignment.is_active ? 'badge-success' : 'badge-secondary'}`}>
                          {assignment.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mb-3">
                        {assignment.description?.substring(0, 100)}...
                      </p>
                      <div className="flex items-center justify-between">
                        <div className="text-xs text-gray-500">
                          {assignment.question_count} questions • {assignment.difficulty}
                        </div>
                        <Link
                          to={`/assignments/${assignment.id}`}
                          className="btn-primary text-xs px-3 py-1"
                        >
                          View Details
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-4">
                  No assignments available at the moment.
                </p>
              )}
            </div>
          </div>

          {/* Recent Submissions */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-medium text-gray-900">My Recent Submissions</h3>
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
                    <div key={submission.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-sm font-medium text-gray-900">
                          {submission.assignment_title}
                        </h4>
                        <span className={`badge ${
                          submission.status === 'submitted' ? 'badge-warning' :
                          submission.status === 'graded' ? 'badge-success' :
                          submission.status === 'draft' ? 'badge-secondary' :
                          'badge-primary'
                        }`}>
                          {submission.status}
                        </span>
                      </div>
                      {submission.total_score && (
                        <div className="flex items-center mb-2">
                          <ChartBarIcon className="h-4 w-4 text-gray-400 mr-1" />
                          <span className="text-sm text-gray-600">
                            Score: {submission.total_score}/{submission.max_possible_score}
                          </span>
                        </div>
                      )}
                      <div className="flex items-center justify-between">
                        <div className="text-xs text-gray-500">
                          {submission.submitted_at ? 
                            `Submitted ${new Date(submission.submitted_at).toLocaleDateString()}` :
                            'Draft'
                          }
                        </div>
                        <Link
                          to={`/submissions/${submission.id}`}
                          className="btn-outline text-xs px-3 py-1"
                        >
                          View Details
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-4">
                  No submissions yet. <Link to="/assignments" className="text-primary-600">Start with an assignment</Link>
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link
              to="/assignments"
              className="bg-primary-500 hover:bg-primary-600 text-white p-6 rounded-lg shadow-sm hover:shadow-md transition-all duration-200"
            >
              <DocumentTextIcon className="h-8 w-8 mb-2" />
              <h3 className="text-lg font-semibold mb-1">Browse Assignments</h3>
              <p className="text-sm opacity-90">Find new assignments to work on</p>
            </Link>
            
            <Link
              to="/viva"
              className="bg-secondary-500 hover:bg-secondary-600 text-white p-6 rounded-lg shadow-sm hover:shadow-md transition-all duration-200"
            >
              <VideoCameraIcon className="h-8 w-8 mb-2" />
              <h3 className="text-lg font-semibold mb-1">Viva Sessions</h3>
              <p className="text-sm opacity-90">Practice or take viva interviews</p>
            </Link>
            
            <Link
              to="/profile"
              className="bg-success-500 hover:bg-success-600 text-white p-6 rounded-lg shadow-sm hover:shadow-md transition-all duration-200"
            >
              <TrophyIcon className="h-8 w-8 mb-2" />
              <h3 className="text-lg font-semibold mb-1">My Progress</h3>
              <p className="text-sm opacity-90">View your learning progress</p>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

export default StudentDashboard
