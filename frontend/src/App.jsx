```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [videoUrl, setVideoUrl] = useState('');
  const [logo, setLogo] = useState(null);
  const [overlayText, setOverlayText] = useState('');
  const [scheduleTime, setScheduleTime] = useState('');
  const [caption, setCaption] = useState('');
  const [pages, setPages] = useState([]);
  const [selectedPages, setSelectedPages] = useState([]);
  const [selectedPlatforms, setSelectedPlatforms] = useState([]);
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const platforms = [
    { id: 'facebook', name: 'Facebook Reels' },
    { id: 'instagram', name: 'Instagram Reels' },
    { id: 'youtube', name: 'YouTube Shorts' },
  ];

  useEffect(() => {
    // Fetch Facebook pages when the component mounts
    const fetchPages = async () => {
      try {
        const response = await axios.get('/api/facebook-pages');
        setPages(response.data.pages || []);
      } catch (error) {
        console.error('Error fetching Facebook pages:', error);
        setMessage('Error fetching Facebook pages. Please ensure you are logged in.');
      }
    };

    fetchPages();
  }, []);

  const handlePageSelection = (e) => {
    const { value, checked } = e.target;
    if (checked) {
      setSelectedPages(prev => [...prev, value]);
    } else {
      setSelectedPages(prev => prev.filter(pageId => pageId !== value));
    }
  };

  const handlePlatformSelection = (e) => {
    const { value, checked } = e.target;
    if (checked) {
      setSelectedPlatforms(prev => [...prev, value]);
    } else {
      setSelectedPlatforms(prev => prev.filter(platformId => platformId !== value));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage('');

    if (selectedPlatforms.length === 0) {
        setMessage('Please select at least one platform to post to.');
        setIsLoading(false);
        return;
    }

    if (selectedPlatforms.includes('facebook') && selectedPages.length === 0) {
        setMessage('Please select at least one Facebook page to post a Reel.');
        setIsLoading(false);
        return;
    }

    const formData = new FormData();
    formData.append('video_url', videoUrl);
    formData.append('overlay_text', overlayText);
    formData.append('caption', caption);
    
    // Append each selected platform
    selectedPlatforms.forEach(platform => {
        formData.append('platforms', platform);
    });
    
    // Append each selected page ID
    selectedPages.forEach(pageId => {
        formData.append('page_ids', pageId);
    });

    if (logo) {
      formData.append('logo', logo);
    }
    if (scheduleTime) {
      formData.append('schedule_time', scheduleTime);
    }

    try {
      const response = await axios.post('/api/post-video', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setMessage(response.data.message);
    } catch (error) {
      console.error('Error posting video:', error);
      setMessage(error.response?.data?.error || 'An error occurred while posting the video.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center p-4">
      <div className="w-full max-w-2xl bg-gray-800 rounded-lg shadow-xl p-8">
        <h1 className="text-3xl font-bold text-center mb-6 text-cyan-400">Multi-Platform Video Automation</h1>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Video URL Input */}
          <div>
            <label htmlFor="videoUrl" className="block text-sm font-medium text-gray-300 mb-1">Video URL (YouTube, etc.)</label>
            <input
              id="videoUrl"
              type="text"
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
              placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
              required
              className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-cyan-500"
            />
          </div>

          {/* Caption Text Area */}
          <div>
            <label htmlFor="caption" className="block text-sm font-medium text-gray-300 mb-1">Video Caption</label>
            <textarea
              id="caption"
              value={caption}
              onChange={(e) => setCaption(e.target.value)}
              placeholder="Write a catchy caption for your video..."
              rows="4"
              className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-cyan-500"
            ></textarea>
          </div>

          {/* Overlay Text and Logo */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="overlayText" className="block text-sm font-medium text-gray-300 mb-1">Overlay Text</label>
              <input
                id="overlayText"
                type="text"
                value={overlayText}
                onChange={(e) => setOverlayText(e.target.value)}
                placeholder="e.g., Follow us for more!"
                className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-cyan-500"
              />
            </div>
            <div>
              <label htmlFor="logo" className="block text-sm font-medium text-gray-300 mb-1">Logo (Optional)</label>
              <input
                id="logo"
                type="file"
                onChange={(e) => setLogo(e.target.files[0])}
                accept="image/png, image/jpeg"
                className="w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-cyan-600 file:text-white hover:file:bg-cyan-700"
              />
            </div>
          </div>
          
          {/* Platform Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Select Target Platforms</label>
            <div className="bg-gray-700 border border-gray-600 rounded-md p-4 space-y-2">
              {platforms.map(platform => (
                <div key={platform.id} className="flex items-center">
                  <input
                    id={`platform-${platform.id}`}
                    type="checkbox"
                    value={platform.id}
                    onChange={handlePlatformSelection}
                    className="h-4 w-4 rounded border-gray-500 bg-gray-600 text-cyan-600 focus:ring-cyan-500"
                  />
                  <label htmlFor={`platform-${platform.id}`} className="ml-3 text-sm text-gray-200">{platform.name}</label>
                </div>
              ))}
            </div>
          </div>

          {/* Facebook Pages Selection (Conditional) */}
          {selectedPlatforms.includes('facebook') && (
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Select Facebook Pages</label>
              <div className="max-h-40 overflow-y-auto bg-gray-700 border border-gray-600 rounded-md p-4 space-y-2">
                {pages.length > 0 ? (
                  pages.map(page => (
                    <div key={page.id} className="flex items-center">
                      <input
                        id={`page-${page.id}`}
                        type="checkbox"
                        value={page.id}
                        onChange={handlePageSelection}
                        className="h-4 w-4 rounded border-gray-500 bg-gray-600 text-cyan-600 focus:ring-cyan-500"
                      />
                      <label htmlFor={`page-${page.id}`} className="ml-3 text-sm text-gray-200">{page.name}</label>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-gray-400">No pages found or still loading...</p>
                )}
              </div>
            </div>
          )}

          {/* Schedule Time */}
          <div>
            <label htmlFor="scheduleTime" className="block text-sm font-medium text-gray-300 mb-1">Schedule Time (Optional)</label>
            <input
              id="scheduleTime"
              type="datetime-local"
              value={scheduleTime}
              onChange={(e) => setScheduleTime(e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-cyan-500"
            />
          </div>

          {/* Submit Button */}
          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-cyan-600 hover:bg-cyan-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-cyan-500 disabled:bg-gray-500 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Processing...' : (scheduleTime ? 'Schedule Video' : 'Post Video Now')}
            </button>
          </div>
        </form>

        {/* Message Display */}
        {message && (
          <div className={`mt-6 text-center text-sm p-3 rounded-md ${message.toLowerCase().includes('error') ? 'bg-red-900 text-red-200' : 'bg-green-900 text-green-200'}`}>
            {message}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
```