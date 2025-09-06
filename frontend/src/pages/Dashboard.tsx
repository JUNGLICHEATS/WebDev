import React from 'react'
import { useAuth } from '../contexts/AuthContext'
import { 
  Shield, 
  Clock, 
  Key, 
  TrendingUp, 
  CheckCircle, 
  AlertTriangle,
  Plus,
  Settings,
  BarChart3,
  Download,
  User,
  LogOut
} from 'lucide-react'

export default function Dashboard() {
  const { user, logout } = useAuth()

  const stats = [
    {
      icon: Shield,
      title: 'Security Score',
      value: '98%',
      trend: '+2%',
      trendType: 'positive',
      description: 'from last week'
    },
    {
      icon: Clock,
      title: 'Active Sessions',
      value: '3',
      trend: 'No change',
      trendType: 'neutral',
      description: 'current sessions'
    },
    {
      icon: Key,
      title: 'API Keys',
      value: '12',
      trend: '+1',
      trendType: 'positive',
      description: 'this month'
    },
    {
      icon: TrendingUp,
      title: 'Total Requests',
      value: '1.2K',
      trend: '+15%',
      trendType: 'positive',
      description: 'this week'
    }
  ]

  const activities = [
    {
      icon: CheckCircle,
      iconColor: 'text-green-600',
      iconBg: 'bg-green-100',
      title: 'Login successful',
      description: 'You signed in from Chrome on Windows',
      time: '2 minutes ago'
    },
    {
      icon: Key,
      iconColor: 'text-blue-600',
      iconBg: 'bg-blue-100',
      title: 'API key generated',
      description: 'New API key created for project "Neural AI"',
      time: '1 hour ago'
    },
    {
      icon: AlertTriangle,
      iconColor: 'text-yellow-600',
      iconBg: 'bg-yellow-100',
      title: 'Security alert',
      description: 'Unusual login attempt from new location',
      time: '3 hours ago'
    }
  ]

  const quickActions = [
    { icon: Key, title: 'Generate API Key', color: 'text-blue-600' },
    { icon: Shield, title: 'Security Settings', color: 'text-green-600' },
    { icon: BarChart3, title: 'View Analytics', color: 'text-purple-600' },
    { icon: Download, title: 'Export Data', color: 'text-orange-600' }
  ]

  const securityItems = [
    { status: 'enabled', text: 'Two-factor authentication enabled' },
    { status: 'enabled', text: 'Strong password policy active' },
    { status: 'enabled', text: 'Email verification completed' },
    { status: 'warning', text: 'Update your recovery email' }
  ]

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Welcome Section */}
      <div className="mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Welcome back, {user?.name}! 👋
            </h1>
            <p className="mt-2 text-gray-600">
              Here's what's happening with your Neural Ninja account today.
            </p>
          </div>
          <div className="mt-4 sm:mt-0">
            <button className="btn-primary flex items-center">
              <Plus className="w-4 h-4 mr-2" />
              New Project
            </button>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat, index) => (
          <div key={index} className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-gradient-to-r from-primary-600 to-secondary-600 rounded-lg flex items-center justify-center">
                  <stat.icon className="w-6 h-6 text-white" />
                </div>
              </div>
              <div className="ml-4 flex-1">
                <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                <div className="flex items-center mt-1">
                  <span className={`text-sm ${
                    stat.trendType === 'positive' ? 'text-green-600' :
                    stat.trendType === 'negative' ? 'text-red-600' :
                    'text-gray-600'
                  }`}>
                    {stat.trend}
                  </span>
                  <span className="text-sm text-gray-500 ml-1">{stat.description}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
        {/* Recent Activity */}
        <div className="lg:col-span-2">
          <div className="card">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900">Recent Activity</h3>
              <button className="btn-secondary text-sm">View All</button>
            </div>
            <div className="space-y-4">
              {activities.map((activity, index) => (
                <div key={index} className="flex items-start space-x-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${activity.iconBg}`}>
                    <activity.icon className={`w-4 h-4 ${activity.iconColor}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900">{activity.title}</p>
                    <p className="text-sm text-gray-600">{activity.description}</p>
                    <p className="text-xs text-gray-500 mt-1">{activity.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="lg:col-span-1">
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">Quick Actions</h3>
            <div className="grid grid-cols-2 gap-3">
              {quickActions.map((action, index) => (
                <button
                  key={index}
                  className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <action.icon className={`w-6 h-6 ${action.color} mb-2`} />
                  <span className="text-sm font-medium text-gray-700 text-center">{action.title}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Security Status */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900">Security Status</h3>
          <div className="flex items-center">
            <span className="text-2xl font-bold text-green-600 mr-2">98%</span>
            <span className="text-sm text-gray-600">Excellent</span>
          </div>
        </div>
        <div className="space-y-3">
          {securityItems.map((item, index) => (
            <div key={index} className="flex items-center">
              {item.status === 'enabled' ? (
                <CheckCircle className="w-5 h-5 text-green-600 mr-3" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-yellow-600 mr-3" />
              )}
              <span className="text-sm text-gray-700">{item.text}</span>
            </div>
          ))}
        </div>
      </div>

      {/* User Profile Section */}
      <div className="mt-8 card">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-gradient-to-r from-primary-600 to-secondary-600 rounded-full flex items-center justify-center">
              <User className="w-6 h-6 text-white" />
            </div>
            <div>
              <h4 className="text-lg font-semibold text-gray-900">{user?.name}</h4>
              <p className="text-sm text-gray-600">{user?.email}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button className="btn-secondary flex items-center">
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </button>
            <button
              onClick={logout}
              className="btn-secondary flex items-center text-red-600 hover:text-red-700 hover:bg-red-50"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Logout
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
