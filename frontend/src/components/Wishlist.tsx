import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { ArrowRight, Heart } from 'lucide-react'

interface SavedItemsPageProps {
  onBack: () => void
}

export function SavedItemsPage({ onBack }: SavedItemsPageProps) {
  const [savedItems, setSavedItems] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadSavedItems()
  }, [])

  const loadSavedItems = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/buy/saved-items/default_user')
      if (response.ok) {
        const data = await response.json()
        setSavedItems(data.saved_items || [])
      }
    } catch (error) {
      console.error('Error loading saved items:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const removeItem = async (itemId: string) => {
    // TODO: Add delete endpoint to backend
    setSavedItems(prev => prev.filter((item: any) => item.$id !== itemId))
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
            <span className="text-sm font-medium">Back to Buy Mode</span>
          </button>
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-pink-500/20 rounded-full flex items-center justify-center">
              <Heart className="w-4 h-4 text-pink-400" />
            </div>
            <span className="text-sm font-medium">Saved Items</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <h1 className="text-display text-4xl font-medium mb-4">💾 Your Saved Items</h1>
            <p className="text-body text-white/60">
              {savedItems.length === 0 
                ? "No saved items yet. Start saving products you love!" 
                : `You have ${savedItems.length} saved item${savedItems.length === 1 ? '' : 's'}`
              }
            </p>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <div className="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin" />
            </div>
          ) : savedItems.length === 0 ? (
            <div className="text-center py-20">
              <div className="w-16 h-16 bg-white/5 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <Heart className="w-8 h-8 text-white/40" />
              </div>
              <h3 className="text-heading text-xl mb-2">No saved items yet</h3>
              <p className="text-body text-white/60 mb-6">
                Go back to Buy Mode and start saving products you love!
              </p>
              <button 
                onClick={onBack}
                className="btn-primary"
              >
                Start Shopping
              </button>
            </div>
          ) : (
            <div className="grid gap-6">
              {savedItems.map((item: any, index) => (
                <motion.div
                  key={item.$id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="glass-card p-6 rounded-xl group"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 space-y-3">
                      <h3 className="text-heading text-xl font-medium text-white">{item.title}</h3>
                      <p className="text-body text-white/70">{item.description}</p>
                      <div className="flex items-center space-x-4">
                        <span className="text-small text-blue-400 capitalize">{item.category}</span>
                        <span className="text-small text-white/40">from {item.store}</span>
                        {item.price > 0 && (
                          <span className="text-small text-green-400">${item.price}</span>
                        )}
                      </div>
                      <div className="flex items-center space-x-3 pt-2">
                        <a 
                          href={item.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="btn-secondary text-sm"
                        >
                          View Product →
                        </a>
                        <button
                          onClick={() => removeItem(item.$id)}
                          className="px-3 py-1 bg-red-500/20 text-red-400 rounded-lg text-small hover:bg-red-500/30 transition-colors"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-small text-white/40">
                        Saved {new Date(item.saved_at).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </main>
    </motion.div>
  )
}
