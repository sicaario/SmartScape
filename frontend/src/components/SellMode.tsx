import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { ArrowRight, Video } from 'lucide-react'

interface SellModeProps {
  onBack: () => void
}

type CurrentStep = 'upload' | 'processing' | 'items' | 'listings' | 'storefront'

interface ExtractedItem {
  name: string
  estimated_price: number
  category: string
  condition: string
  confidence?: number
  frame_data?: string
  timestamp?: number
}

interface Storefront {
  posted_count?: number
  total_potential_income?: number
  failed_count?: number
  listings?: any[]
  failed_listings?: any[]
  next_steps?: string[]
}

export function SellMode({ onBack }: SellModeProps) {
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [jobId, setJobId] = useState<string | null>(null)
  const [extractedItems, setExtractedItems] = useState<ExtractedItem[]>([])
  const [storefront, setStorefront] = useState<Storefront | null>(null)
  const [currentStep, setCurrentStep] = useState<CurrentStep>('upload')
  const [editingItem, setEditingItem] = useState<number | null>(null)
  const [showLoginForm, setShowLoginForm] = useState(false)
  const [loginCredentials, setLoginCredentials] = useState({ email: '', password: '' })
  const [error, setError] = useState<string | null>(null)

  const handleVideoUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setIsUploading(true)
    setUploadProgress(0)
    setCurrentStep('processing')
    setError(null)
    
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await fetch('http://localhost:8000/api/sell/upload-video', {
        method: 'POST',
        body: formData,
      })
      
      if (!response.ok) {
        throw new Error(`Failed to upload video: ${response.statusText}`)
      }
      
      const data = await response.json()
      setJobId(data.job_id)
      
      pollExtractionStatus(data.job_id)
      
    } catch (error) {
      console.error('Error uploading video:', error)
      setError(error instanceof Error ? error.message : 'Failed to upload video')
      setIsUploading(false)
      setCurrentStep('upload')
    }
  }

  const pollExtractionStatus = async (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/sell/extraction-status/${jobId}`)
        
        if (!response.ok) {
          throw new Error(`Failed to get status: ${response.statusText}`)
        }
        
        const data = await response.json()
        setUploadProgress(data.progress || 0)
        
        if (data.status === 'completed') {
          clearInterval(interval)
          setIsUploading(false)
          setExtractedItems(data.items || [])
          setCurrentStep('items')
        } else if (data.status === 'failed') {
          clearInterval(interval)
          setIsUploading(false)
          setCurrentStep('upload')
          setError(data.error || 'Extraction failed')
        }
      } catch (error) {
        console.error('Error polling status:', error)
        clearInterval(interval)
        setIsUploading(false)
        setCurrentStep('upload')
        setError(error instanceof Error ? error.message : 'Failed to check status')
      }
    }, 1000)

    setTimeout(() => {
      clearInterval(interval)
      if (isUploading) {
        setIsUploading(false)
        setCurrentStep('upload')
        setError('Processing timed out')
      }
    }, 300000)
  }

  const createStorefront = async () => {
    if (!jobId || !loginCredentials.email.trim()) return
    
    try {
      setError(null)
      const response = await fetch('http://localhost:8000/api/sell/create-storefront', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          job_id: jobId,
          email: loginCredentials.email.trim(),
          password: loginCredentials.password
        }),
      })
      
      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to post to UseThis')
      }
      
      setStorefront(data)
      setCurrentStep('storefront')
      setShowLoginForm(false)
      
    } catch (error) {
      console.error('Error creating storefront:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to create storefront'
      setError(errorMessage)
      alert(`Error: ${errorMessage}`)
    }
  }

  const updateItem = (index: number, field: keyof ExtractedItem, value: string | number) => {
    setExtractedItems(prev => prev.map((item, i) => 
      i === index ? { ...item, [field]: value } : item
    ))
  }

  const deleteItem = async (index: number) => {
    if (!jobId) return
    
    try {
      setError(null)
      const response = await fetch('http://localhost:8000/api/sell/delete-item', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          job_id: jobId,
          item_index: index
        }),
      })
      
      if (response.ok) {
        setExtractedItems(prev => prev.filter((_, i) => i !== index))
      } else {
        throw new Error(`Failed to delete item: ${response.statusText}`)
      }
    } catch (error) {
      console.error('Error deleting item:', error)
      setError(error instanceof Error ? error.message : 'Failed to delete item')
    }
  }

  const saveItemEdit = async (index: number) => {
    if (!jobId || index >= extractedItems.length) return
    
    const item = extractedItems[index]
    
    try {
      setError(null)
      const response = await fetch('http://localhost:8000/api/sell/update-item', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          job_id: jobId,
          item_index: index,
          name: item.name,
          estimated_price: item.estimated_price
        }),
      })
      
      if (response.ok) {
        setEditingItem(null)
      } else {
        throw new Error(`Failed to update item: ${response.statusText}`)
      }
    } catch (error) {
      console.error('Error updating item:', error)
      setError(error instanceof Error ? error.message : 'Failed to update item')
      setEditingItem(null)
    }
  }

  const resetToUpload = () => {
    setCurrentStep('upload')
    setError(null)
    setIsUploading(false)
    setUploadProgress(0)
    setJobId(null)
    setExtractedItems([])
    setStorefront(null)
    setEditingItem(null)
    setShowLoginForm(false)
    setLoginCredentials({ email: '', password: '' })
  }

  return (
    <motion.div
      initial={{ x: '100%' }}
      animate={{ x: 0 }}
      exit={{ x: '100%' }}
      transition={{ type: 'spring', damping: 30, stiffness: 300 }}
      className="min-h-screen flex flex-col"
    >
      {/* Header */}
      <header className="p-6 border-b border-white/10">
        <div className="flex items-center justify-between max-w-6xl mx-auto">
          <button 
            onClick={onBack} 
            className="flex items-center text-white/60 hover:text-white transition-colors group"
          >
            <ArrowRight className="w-4 h-4 mr-2 rotate-180 transition-transform group-hover:-translate-x-1" />
            <span className="text-sm font-medium">Back to Home</span>
          </button>
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-purple-500/20 rounded-full flex items-center justify-center">
              <Video className="w-4 h-4 text-purple-400" />
            </div>
            <span className="text-sm font-medium">Sell Mode — Declutter Assistant</span>
          </div>
        </div>
      </header>

      {/* Error Display */}
      {error && (
        <div className="p-4 mx-6 mt-4 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400">
          <div className="flex justify-between items-center">
            <span>{error}</span>
            <button 
              onClick={() => setError(null)}
              className="text-red-400 hover:text-red-300 ml-4"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 p-6">
        <div className="max-w-4xl mx-auto">
          
          {/* Upload Step */}
          {currentStep === 'upload' && (
            <div className="flex items-center justify-center min-h-[60vh]">
              <div className="max-w-2xl w-full space-y-12">
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
                  className="text-center space-y-4"
                >
                  <h2 className="text-display text-5xl font-medium tracking-tight">Declutter Your Space</h2>
                  <p className="text-body text-xl text-white/60 max-w-lg mx-auto">
                    Upload a video of your room and I'll identify sellable items, 
                    create listings, and handle negotiations for you.
                  </p>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2, duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
                  className="glass-card rounded-3xl p-12"
                >
                  <label className="flex flex-col items-center justify-center h-80 border-2 border-dashed border-white/20 rounded-2xl cursor-pointer hover:border-white/40 transition-colors group">
                    <div className="w-16 h-16 bg-purple-500/20 rounded-2xl flex items-center justify-center mb-6 group-hover:bg-purple-500/30 transition-colors">
                      <Video className="w-8 h-8 text-purple-400" />
                    </div>
                    <span className="text-display text-2xl font-medium mb-2">Upload Room Video</span>
                    <span className="text-body text-white/60 mb-4">Record a walkthrough of your space</span>
                    <span className="text-sm text-white/40">MP4, MOV up to 100MB</span>
                    <input
                      type="file"
                      accept="video/*"
                      onChange={handleVideoUpload}
                      className="hidden"
                    />
                  </label>
                </motion.div>
              </div>
            </div>
          )}

          {/* Processing Step */}
          {currentStep === 'processing' && (
            <div className="flex items-center justify-center min-h-[60vh]">
              <div className="max-w-2xl w-full">
                <div className="glass-card rounded-3xl p-12 text-center space-y-8">
                  <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center mx-auto">
                    <Video className="w-8 h-8 text-white" />
                  </div>
                  
                  <div className="space-y-4">
                    <h3 className="text-display text-2xl font-medium">Processing Video...</h3>
                    
                    <div className="w-full bg-white/10 rounded-full h-2">
                      <motion.div
                        className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full"
                        initial={{ width: 0 }}
                        animate={{ width: `${uploadProgress}%` }}
                        transition={{ duration: 0.3, ease: "easeOut" }}
                      />
                    </div>
                    
                    <p className="text-body text-white/60">
                      {uploadProgress < 30 ? 'Extracting frames from video...' : 
                       uploadProgress < 60 ? 'Detecting objects with AI...' : 
                       uploadProgress < 80 ? 'Filtering sellable items...' : 
                       uploadProgress < 100 ? 'Finalizing results...' :
                       'Processing complete!'}
                    </p>

                    <button
                      onClick={resetToUpload}
                      className="btn-secondary mt-4"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Extracted Items Step */}
          {currentStep === 'items' && (
            <div className="space-y-8">
              <div className="text-center">
                <h2 className="text-display text-4xl font-medium mb-4">Found Sellable Items</h2>
                <p className="text-body text-white/60">I found {extractedItems.length} items that could be sold</p>
                <p className="text-small text-white/40 mt-2">Click on names or prices to edit them</p>
              </div>

              <div className="space-y-6">
                {extractedItems.map((item, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="glass-card p-6 rounded-xl relative group"
                  >
                    <button
                      onClick={() => deleteItem(index)}
                      className="absolute top-2 right-2 w-8 h-8 bg-red-500/20 hover:bg-red-500/40 text-red-400 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-200"
                      title="Delete item"
                    >
                      ×
                    </button>

                    <div className="space-y-4">
                      <div className="aspect-video bg-white/5 rounded-lg flex items-center justify-center">
                        {item.frame_data ? (
                          <img 
                            src={`data:image/jpeg;base64,${item.frame_data}`} 
                            alt={item.name}
                            className="w-full h-full object-cover rounded-lg"
                          />
                        ) : (
                          <span className="text-white/40">Frame @ {item.timestamp}s</span>
                        )}
                      </div>
                      <div>
                        {editingItem === index ? (
                          <div className="space-y-2">
                            <input
                              type="text"
                              value={item.name}
                              onChange={(e) => updateItem(index, 'name', e.target.value)}
                              className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 text-lg font-medium"
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') saveItemEdit(index)
                                if (e.key === 'Escape') setEditingItem(null)
                              }}
                              autoFocus
                            />
                            <input
                              type="number"
                              value={item.estimated_price}
                              onChange={(e) => updateItem(index, 'estimated_price', parseFloat(e.target.value) || 0)}
                              className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-green-400 font-medium"
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') saveItemEdit(index)
                                if (e.key === 'Escape') setEditingItem(null)
                              }}
                              step="0.01"
                              min="0"
                            />
                            <div className="flex gap-2">
                              <button 
                                onClick={() => saveItemEdit(index)}
                                className="px-3 py-1 bg-green-500/20 text-green-400 rounded text-sm hover:bg-green-500/30 transition-colors"
                              >
                                Save
                              </button>
                              <button 
                                onClick={() => setEditingItem(null)}
                                className="px-3 py-1 bg-white/10 text-white/60 rounded text-sm hover:bg-white/20 transition-colors"
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div>
                            <h3 
                              className="text-heading text-lg font-medium capitalize cursor-pointer hover:text-blue-400 transition-colors"
                              onClick={() => setEditingItem(index)}
                            >
                              {item.name}
                            </h3>
                            <p className="text-small text-white/60 capitalize">{item.category} • {item.condition}</p>
                            <p 
                              className="text-body text-green-400 font-medium cursor-pointer hover:text-green-300 transition-colors"
                              onClick={() => setEditingItem(index)}
                            >
                              ${item.estimated_price}
                            </p>
                            {item.confidence && (
                              <p className="text-small text-white/40">Confidence: {Math.round(item.confidence * 100)}%</p>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>

              <div className="text-center">
                {!showLoginForm ? (
                  <motion.button
                    onClick={() => setShowLoginForm(true)}
                    className="btn-primary"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    Post to UseThis
                  </motion.button>
                ) : (
                  <div className="glass-card p-6 rounded-xl max-w-md mx-auto">
                    <h3 className="text-heading text-xl mb-4">Login to UseThis</h3>
                    <div className="space-y-4">
                      <input
                        type="email"
                        placeholder="Your UseThis email"
                        value={loginCredentials.email}
                        onChange={(e) => setLoginCredentials(prev => ({ ...prev, email: e.target.value }))}
                        className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50"
                        required
                      />
                      <input
                        type="password"
                        placeholder="Password (optional)"
                        value={loginCredentials.password}
                        onChange={(e) => setLoginCredentials(prev => ({ ...prev, password: e.target.value }))}
                        className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50"
                      />
                      <div className="flex gap-3">
                        <button
                          onClick={createStorefront}
                          className="btn-primary flex-1"
                          disabled={!loginCredentials.email.trim()}
                        >
                          Post Items
                        </button>
                        <button
                          onClick={() => setShowLoginForm(false)}
                          className="btn-secondary"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Storefront Step */}
          {currentStep === 'storefront' && storefront && (
            <div className="space-y-8">
              <div className="text-center">
                <h2 className="text-display text-4xl font-medium mb-4">🎉 Posted to UseThis!</h2>
                <p className="text-body text-white/60">Your items are now live on the student rental marketplace</p>
                <a 
                  href="https://use-this.netlify.app" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="inline-block mt-4 text-blue-400 hover:text-blue-300 transition-colors"
                >
                  Visit UseThis Platform →
                </a>
              </div>

              <div className="grid md:grid-cols-4 gap-4 mb-8">
                <div className="glass-card p-4 text-center">
                  <div className="text-2xl font-bold text-green-400">{storefront.posted_count || 0}</div>
                  <div className="text-small text-white/60">Items Posted</div>
                </div>
                <div className="glass-card p-4 text-center">
                  <div className="text-2xl font-bold text-blue-400">${storefront.total_potential_income || 0}</div>
                  <div className="text-small text-white/60">Monthly Potential</div>
                </div>
                <div className="glass-card p-4 text-center">
                  <div className="text-2xl font-bold text-purple-400">{storefront.failed_count || 0}</div>
                  <div className="text-small text-white/60">Failed Posts</div>
                </div>
                <div className="glass-card p-4 text-center">
                  <div className="text-2xl font-bold text-yellow-400">Live</div>
                  <div className="text-small text-white/60">Status</div>
                </div>
              </div>

              <div className="glass-card p-6 rounded-xl text-center">
                <h3 className="text-heading text-xl mb-2">🚀 What's Next?</h3>
                <div className="flex justify-center gap-4">
                  <a 
                    href="https://use-this.netlify.app" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="btn-primary"
                  >
                    Manage on UseThis
                  </a>
                  <button 
                    className="btn-secondary"
                    onClick={resetToUpload}
                  >
                    Add More Items
                  </button>
                </div>
              </div>
            </div>
          )}

        </div>
      </main>
    </motion.div>
  )
}
