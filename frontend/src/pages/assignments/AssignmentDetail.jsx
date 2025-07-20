import React from 'react'
import { useParams } from 'react-router-dom'
import LoadingSpinner from '../../components/LoadingSpinner'

const AssignmentDetail = () => {
  const { id } = useParams()

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="card">
          <div className="card-body">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Assignment Details</h1>
            <p className="text-gray-600">Assignment ID: {id}</p>
            <p className="text-gray-500 mt-4">This component is under development.</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AssignmentDetail
