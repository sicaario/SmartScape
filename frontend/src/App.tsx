import React, { useState, useEffect } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { LandingPage } from './components/Home'
import { BuyMode } from './components/BuyMode'
import { SavedItemsPage } from './components/Wishlist'
import { SellMode } from './components/SellMode'
import { X, AlertCircle } from 'lucide-react'
import './App.css'

type AppMode = 'landing' | 'buy' | 'sell' | 'saved'

function App() {
  const [mode, setMode] = useState<AppMode>('landing')
  const [showDeploymentModal, setShowDeploymentModal] = useState(false)

  useEffect(() => {
    // Check if user has seen the deployment notice
    const hasSeenNotice = localStorage.getItem('SmartScape-deployment-notice')
    if (!hasSeenNotice) {
      setShowDeploymentModal(true)
    }
  }, [])

  const handleCloseModal = () => {
    setShowDeploymentModal(false)
    localStorage.setItem('SmartScape-deployment-notice', 'true')
  }

  return (
    <div className="min-h-screen bg-black text-white overflow-hidden noise">
      <div className="dynamic-bg" />
      
      {/* Deployment Notice Modal */}
      <AnimatePresence>
        {showDeploymentModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            style={{ backgroundColor: 'rgba(0, 0, 0, 0.8)' }}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="glass-card max-w-2xl w-full p-8 rounded-2xl relative"
            >
              <button
                onClick={handleCloseModal}
                className="absolute top-4 right-4 w-8 h-8 flex items-center justify-center text-white/60 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>

              <div className="space-y-6">
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-blue-500/20 rounded-full flex items-center justify-center">
                    <AlertCircle className="w-6 h-6 text-blue-400" />
                  </div>
                  <h2 className="text-heading text-2xl">Frontend Demo Notice</h2>
                </div>

                <div className="space-y-4 text-body text-white/80 leading-relaxed">
                  <p>
                    Welcome to SmartScape! This is currently a <strong>frontend-only demonstration</strong> 
                    of our AI-powered home concierge platform.
                  </p>
                  
                  <p>
                    While the entire SmartScape pipeline works smoothly in our local development environment, 
                    we weren't able to deploy the full backend due to compatibility issues with machine learning 
                    libraries on platforms like Render.
                  </p>
                  
                  <p>
                    Specifically, the OpenCV-based video processing and some AI dependencies (used for frame 
                    extraction and Nebius model integration) exceeded the resource or compatibility limits of 
                    most free-tier hosting services.
                  </p>
                  
                  <p>
                    As a result, we opted to focus on a seamless local demo and documented deployment steps 
                    for future scaling. You can explore the beautiful UI and see how the platform would work!
                  </p>
                  
                  <p>
                    <a 
                      href="https://youtu.be/NUEluIMwpCk" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:text-blue-300 transition-colors underline"
                    >
                      Watch our full demo video
                    </a> to see SmartScape in action locally!
                  </p>
                </div>

                <div className="flex items-center justify-center pt-4">
                  <button
                    onClick={handleCloseModal}
                    className="btn-primary"
                  >
                    Got it, let's explore!
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence mode="wait">
        {mode === 'landing' && (
          <LandingPage key="landing" onModeSelect={setMode} />
        )}
        {mode === 'buy' && (
          <BuyMode key="buy" onBack={() => setMode('landing')} onSavedClick={() => setMode('saved')} />
        )}
        {mode === 'sell' && (
          <SellMode key="sell" onBack={() => setMode('landing')} />
        )}
        {mode === 'saved' && (
          <SavedItemsPage key="saved" onBack={() => setMode('buy')} />
        )}
      </AnimatePresence>
    </div>
  )
}

export default App
