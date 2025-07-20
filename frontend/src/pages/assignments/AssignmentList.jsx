import React from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from 'react-query'
import { assignmentsAPI } from '../../services/api'
import { useAuth } from '../../contexts/AuthContext'
import LoadingSpinner from '../../components/LoadingSpinner'
import { DocumentTextIcon, PlusIcon } from '@heroicons/react/24/outline'

const AssignmentList = () => {
  const { isTeacher } = useAuth()

  const { data: assignments, isLoading, error } = useQuery(
    'assignments',
    assignmentsAPI.list,
    {
      refetchOnWindowFocus: false,
    }
  )

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" text="Loading assignments..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h3 className="text-lg font-medium text-gray-900">Error loading assignments</h3>
          <p className="text-gray-500">Please try again later.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Assignments</h1>
            <p className="mt-2 text-gray-600">
              {isTeacher ? 'Manage your assignments' : 'Browse available assignments'}
            </p>
          </div>
          {isTeacher && (
            <Link to="/assignments/create" className="btn-primary">
              <PlusIcon className="h-5 w-5 mr-2" />
              Create Assignment
            </Link>
          )}
        </div>

        {assignments?.data?.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {assignments.data.map((assignment) => (
              <div key={assignment.id} className="assignment-card">
                <div className="card-body">
                  <div className="flex items-center justify-between mb-4">
                    <DocumentTextIcon className="h-8 w-8 text-primary-600" />
                    <span className={`badge ${assignment.is_active ? 'badge-success' : 'badge-secondary'}`}>
                      {assignment.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {assignment.title}
                  </h3>
                  <p className="text-gray-600 text-sm mb-4">
                    {assignment.description?.substring(0, 150)}...
                  </p>
                  <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                    <span>{assignment.question_count} questions</span>
                    <span className="capitalize">{assignment.difficulty}</span>
                  </div>
                  <Link
                    to={`/assignments/${assignment.id}`}
                    className="btn-primary w-full text-center"
                  >
                    View Details
                  </Link>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No assignments</h3>
            <p className="mt-1 text-sm text-gray-500">
              {isTeacher ? 'Get started by creating a new assignment.' : 'No assignments available at the moment.'}
            </p>
            {isTeacher && (
              <div className="mt-6">
                <Link to="/assignments/create" className="btn-primary">
                  <PlusIcon className="h-5 w-5 mr-2" />
                  Create Assignment
                </Link>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default AssignmentList
