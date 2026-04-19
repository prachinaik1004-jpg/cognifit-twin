import { useState, useEffect } from 'react';
import { HiArrowLeft, HiCheck, HiXMark, HiArrowPath, HiClock } from 'react-icons/hi2';
import { getAuthUrl, handleCallback, syncWearableData, getWearableStatus } from '../services/wearable';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

export default function Settings({ switchView, user }) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState(null);

  useEffect(() => {
    async function checkStatus() {
      try {
        console.log('Checking wearable status for user:', user?.id);
        const data = await getWearableStatus(user?.id);
        console.log('Wearable status result:', data);
        setStatus(data);
      } catch (error) {
        console.error('Failed to check status:', error);
      }
    }
    checkStatus();
    
    // Also check status every 2 seconds for 10 seconds after mount (to catch OAuth callback)
    const interval = setInterval(checkStatus, 2000);
    const timeout = setTimeout(() => clearInterval(interval), 10000);
    
    return () => {
      clearInterval(interval);
      clearTimeout(timeout);
    };
  }, [user?.id]);

  const handleConnect = async () => {
    setLoading(true);
    try {
      const data = await getAuthUrl(user?.id);
      window.location.href = data.auth_url;
    } catch (error) {
      console.error('Failed to get auth URL:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    setSyncResult(null);
    try {
      const result = await syncWearableData(user?.id);
      setSyncResult(result);
      // Refresh status after sync
      const newStatus = await getWearableStatus(user?.id);
      setStatus(newStatus);
    } catch (error) {
      console.error('Failed to sync:', error);
      setSyncResult({ success: false, error: error.message });
    } finally {
      setSyncing(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      await axios.delete(`${API_BASE}/wearable/disconnect`, {
        params: { user_id: user?.id }
      });
      setStatus({ connected: false, provider: null });
      setSyncResult(null);
    } catch (error) {
      console.error('Failed to disconnect:', error);
    }
  };

  return (
    <div className="p-6 max-w-2xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <button
          onClick={() => switchView('Chat')}
          className="p-2 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
        >
          <HiArrowLeft className="text-xl text-text-main" />
        </button>
        <div>
          <h1 className="font-serif text-2xl text-text-main">Settings</h1>
          <p className="text-sm text-text-muted">Manage your connections and preferences</p>
        </div>
      </div>

      {/* Google Fit Section */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${status?.connected ? 'bg-green-100' : 'bg-gray-100'}`}>
              {status?.connected ? (
                <HiCheck className="text-green-600 text-lg" />
              ) : (
                <HiXMark className="text-gray-400 text-lg" />
              )}
            </div>
            <div>
              <h3 className="font-semibold text-text-main">Google Fit</h3>
              <p className="text-sm text-text-muted">
                {status?.connected ? 'Connected' : 'Not connected'}
              </p>
            </div>
          </div>
          {status?.connected && (
            <button
              onClick={handleSync}
              disabled={syncing}
              className="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-200 text-sm font-medium hover:bg-gray-50 transition-colors cursor-pointer disabled:opacity-50"
            >
              <HiArrowPath className={`text-base ${syncing ? 'animate-spin' : ''}`} />
              {syncing ? 'Syncing...' : 'Sync'}
            </button>
          )}
        </div>

        {/* Connection Status */}
        {status?.connected && (
          <div className="bg-gray-50 rounded-xl p-4 mb-4">
            <div className="flex items-center gap-2 text-sm text-text-muted mb-2">
              <HiClock className="text-base" />
              Last sync: {status.last_sync ? new Date(status.last_sync).toLocaleString() : 'Never'}
            </div>
          </div>
        )}

        {/* Sync Result */}
        {syncResult && (
          <div className={`rounded-xl p-4 mb-4 ${syncResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
            <p className={`text-sm ${syncResult.success ? 'text-green-800' : 'text-red-800'}`}>
              {syncResult.success
                ? `Synced ${syncResult.steps} days of steps, ${syncResult.heart_rate} days of heart rate, ${syncResult.sleep} days of sleep data`
                : `Sync failed: ${syncResult.error}`}
            </p>
          </div>
        )}

        {/* Connect Button */}
        {!status?.connected && (
          <button
            onClick={handleConnect}
            disabled={loading}
            className="w-full py-3 rounded-xl bg-primary text-white font-medium hover:bg-primary-hover transition-colors cursor-pointer disabled:opacity-50"
          >
            {loading ? 'Connecting...' : 'Connect Google Fit'}
          </button>
        )}

        {/* Disconnect */}
        {status?.connected && (
          <button
            onClick={handleDisconnect}
            className="w-full py-3 rounded-xl border border-red-200 text-red-600 font-medium hover:bg-red-50 transition-colors cursor-pointer"
          >
            Disconnect
          </button>
        )}

        {/* Info */}
        <div className="mt-4 text-xs text-text-muted">
          <p>Connect Google Fit to sync your steps, heart rate, and sleep data.</p>
          <p className="mt-1">Your data is stored securely and used to provide personalized health insights.</p>
        </div>
      </div>
    </div>
  );
}
