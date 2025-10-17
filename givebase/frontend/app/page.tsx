'use client';

import { createBaseAccountSDK } from '@base-org/account';
import { useEffect, useState } from 'react';
import { baseSepolia } from 'viem/chains';
import { encodeFunctionData, parseUnits } from 'viem';

const USDC_ADDRESS = '0x036CbD53842c5426634e7929541eC2318f3dCF7e';
const CHAIN_ID = 84532;

const ERC20_ABI = [{
  inputs: [
    { name: 'to', type: 'address' },
    { name: 'amount', type: 'uint256' }
  ],
  name: 'transfer',
  outputs: [{ name: '', type: 'bool' }],
  stateMutability: 'nonpayable',
  type: 'function'
}] as const;

interface Campaign {
  id: number;
  title: string;
  description: string;
  emoji: string;
  recipient_address: string;
  raised_amount: string;
  goal_amount: string;
  progress: number;
}

interface Donation {
  id: number;
  campaign_title: string;
  campaign_emoji: string;
  amount: string;
  tx_hash: string;
  used_sub_account: boolean;
  created_at: string;
}

interface Stats {
  total_donated: string;
  total_donors: number;
  sub_account_donations: number;
  sub_account_percentage: number;
}

export default function QuickGive() {
  const [provider, setProvider] = useState<any>(null);
  const [universalAddress, setUniversalAddress] = useState('');
  const [subAccountAddress, setSubAccountAddress] = useState('');
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [donations, setDonations] = useState<Donation[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null);
  const [amount, setAmount] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');
  const [showSuccess, setShowSuccess] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  useEffect(() => {
    const sdk = createBaseAccountSDK({
      appName: 'QuickGive - Auto Spend Demo',
      appLogoUrl: 'https://base.org/logo.png',
      appChainIds: [baseSepolia.id],
      subAccounts: {
        creation: 'on-connect',
        defaultAccount: 'sub'
      }
    });

    setProvider(sdk.getProvider());
    loadCampaigns();
    loadStats();
  }, []);

  useEffect(() => {
    if (universalAddress) {
      loadUserDonations();
    }
  }, [universalAddress]);

  useEffect(() => {
    const interval = setInterval(loadStats, 10000);
    return () => clearInterval(interval);
  }, []);

  async function loadCampaigns() {
    try {
      const res = await fetch('/api/campaigns');
      const data = await res.json();
      setCampaigns(data.campaigns || []);
    } catch (error) {
      console.error('Failed to load campaigns:', error);
    }
  }

  async function loadStats() {
    try {
      const res = await fetch('/api/stats');
      const data = await res.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  }

  async function loadUserDonations() {
    try {
      const res = await fetch(`/api/user-donations?address=${universalAddress}`);
      const data = await res.json();
      setDonations(data.donations || []);
    } catch (error) {
      console.error('Failed to load donations:', error);
    }
  }

  async function connectWallet() {
    if (!provider) return;
    
    setLoading(true);
    setStatus('Connecting...');
    
    try {
      await provider.request({ method: 'wallet_connect', params: [] });
      
      const accounts = await provider.request({
        method: 'eth_requestAccounts',
        params: []
      });

      const sub = accounts[0];
      const universal = accounts[1] || accounts[0];
      
      setSubAccountAddress(sub);
      setUniversalAddress(universal);
      setStatus('Connected!');

      // Save sub account
      await fetch('/api/update-sub-account', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          wallet_address: universal,
          sub_account_address: sub
        })
      });
    } catch (error: any) {
      setStatus('Connection failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  }

  async function fundSubAccount() {
    if (!provider || !subAccountAddress || !universalAddress) return;

    setLoading(true);
    setStatus('Funding Sub Account with 1 USDC...');

    try {
      // Transfer 1 USDC from Universal to Sub Account
      const oneUSDC = parseUnits('1', 6);
      
      const data = encodeFunctionData({
        abi: ERC20_ABI,
        functionName: 'transfer',
        args: [subAccountAddress as `0x${string}`, oneUSDC]
      });

      const callsId = await provider.request({
        method: 'wallet_sendCalls',
        params: [{
          version: '2.0.0',
          atomicRequired: true,
          chainId: `0x${CHAIN_ID.toString(16)}`,
          from: universalAddress, // Send FROM universal account
          calls: [{
            to: USDC_ADDRESS,
            data: data,
            value: '0x0'
          }]
        }]
      });

      console.log('✅ Funding transaction sent:', callsId);
      setStatus('✅ Sub Account funded! You can now donate.');
      
      // Wait a bit for the transaction to confirm
      await new Promise(resolve => setTimeout(resolve, 3000));
      
    } catch (error: any) {
      console.error('Funding error:', error);
      setStatus('❌ Funding failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  }

  async function donate() {
    if (!provider || !selectedCampaign || !amount) return;

    setLoading(true);
    setStatus('Processing donation...');

    try {
      const amountInUnits = parseUnits(amount, 6);
      
      const data = encodeFunctionData({
        abi: ERC20_ABI,
        functionName: 'transfer',
        args: [selectedCampaign.recipient_address as `0x${string}`, amountInUnits]
      });

      console.log('Sending from Sub Account:', subAccountAddress);
      console.log('To:', selectedCampaign.recipient_address);
      console.log('Amount:', amount, 'USDC');

      let callsId;
      
      try {
        callsId = await provider.request({
          method: 'wallet_sendCalls',
          params: [{
            version: '2.0',
            atomicRequired: true,
            chainId: `0x${CHAIN_ID.toString(16)}`,
            from: subAccountAddress,
            calls: [{
              to: USDC_ADDRESS,
              data: data,
              value: '0x0'
            }]
          }]
        });
      } catch (sendError: any) {
        console.error('Send calls error:', sendError);
        console.error('Send error type:', typeof sendError);
        console.error('Send error constructor:', sendError?.constructor?.name);
        console.error('Send error keys:', Object.keys(sendError || {}));
        
        // Check for specific errors
        if (sendError?.code === 4001 || sendError?.code === 'ACTION_REJECTED') {
          throw new Error('User cancelled the transaction');
        }
        
        // Gas estimation failure - check if it's a spend permission limit issue
        if (sendError?.message?.includes('execution reverted') || sendError?.message?.includes('gas')) {
          // Check total donations today
          const todaysDonations = donations.filter(d => {
            const donationDate = new Date(d.created_at);
            const today = new Date();
            return donationDate.toDateString() === today.toDateString();
          });
          
          const totalToday = todaysDonations.reduce((sum, d) => sum + parseFloat(d.amount), 0);
          const newTotal = totalToday + parseFloat(amount);
          
          if (newTotal > 10) {
            throw new Error(
              `Daily spend limit reached!\n\n` +
              `You've donated ${totalToday.toFixed(2)} today.\n` +
              `Trying to donate ${amount} more would exceed the $10/day limit.\n\n` +
              `The spend permission allows up to $10 USDC per day.\n` +
              `Please wait until tomorrow or donate a smaller amount.`
            );
          }
          
          throw new Error(
            'Transaction failed during gas estimation.\n\n' +
            'This usually means:\n' +
            '1. Your Universal Account ran out of USDC or ETH\n' +
            '2. The spend permission expired or was revoked\n' +
            `3. Your Sub Account (${subAccountAddress}) needs a small USDC balance\n\n` +
            'Try refreshing the page and reconnecting your wallet.'
          );
        }
        
        throw sendError || new Error('Transaction failed to send');
      }

      console.log('✅ Transaction submitted:', callsId);

      // Poll for status
      let txHash = callsId;
      let statusCheckAttempts = 0;
      const maxAttempts = 15;
      
      const pollStatus = async () => {
        if (statusCheckAttempts >= maxAttempts) {
          console.log('Status polling timeout - proceeding anyway');
          return;
        }
        
        statusCheckAttempts++;
        
        try {
          const status = await provider.request({
            method: 'wallet_getCallsStatus',
            params: [callsId]
          });

          console.log(`Status check ${statusCheckAttempts}:`, status.status);

          if (status.status === 'CONFIRMED') {
            if (status.receipts && status.receipts[0] && status.receipts[0].transactionHash) {
              txHash = status.receipts[0].transactionHash;
              console.log('✅ Transaction confirmed with hash:', txHash);
            }
            return;
          } else if (status.status === 'FAILED') {
            throw new Error('Transaction failed on-chain');
          } else if (status.status === 'PENDING') {
            await new Promise(resolve => setTimeout(resolve, 2000));
            return pollStatus();
          }
        } catch (statusError) {
          console.log('Status check error:', statusError);
        }
      };
      
      await pollStatus();

      const isFirstDonation = donations.length === 0;
      
      setSuccessMessage(
        isFirstDonation
          ? `✅ First donation of $${amount} completed! Future donations will be instant if you enabled auto-spend.`
          : `✨ Instant donation of $${amount} completed! No wallet pop-ups needed!`
      );
      setShowSuccess(true);
      setSelectedCampaign(null);
      setAmount('');
      
      // Record donation
      await fetch('/api/record-donation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          donor_address: universalAddress,
          sub_account_address: subAccountAddress,
          campaign_id: selectedCampaign.id,
          amount: amount,
          tx_hash: txHash,
          used_spend_permission: !isFirstDonation
        })
      });

      loadCampaigns();
      loadStats();
      loadUserDonations();
    } catch (error: any) {
      console.error('Donation error:', error);
      console.error('Error details:', {
        message: error?.message,
        code: error?.code,
        data: error?.data,
        stack: error?.stack
      });
      
      // Check if user rejected
      if (error?.code === 4001 || error?.message?.includes('user rejected') || error?.message?.includes('User rejected')) {
        setStatus('❌ Transaction cancelled by user');
        return;
      }
      
      if (error?.message?.includes('execution reverted') || error?.message?.includes('gas')) {
        setStatus(
          `⚠️ Transaction Failed\n\n` +
          `Common issues:\n` +
          `1. Your Universal Account needs USDC\n` +
          `   Get USDC: https://faucet.circle.com/\n\n` +
          `2. Your Universal Account needs ETH for gas\n` +
          `   Get ETH: https://www.alchemy.com/faucets/base-sepolia\n\n` +
          `3. Check that auto-spend permissions are still valid`
        );
      } else if (error?.message?.includes('insufficient')) {
        setStatus('❌ Insufficient balance in your Universal Account');
      } else {
        // Generic error
        setStatus(`❌ Donation failed${error?.message ? ': ' + error.message : ' - check console for details'}`);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 to-blue-900 p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <header className="text-center mb-12">
          <div className="flex items-center justify-center gap-4 mb-4">
            <h1 className="text-5xl md:text-6xl font-black text-white">
              ⚡ QuickGive
            </h1>
            <span className="bg-gradient-to-r from-green-400 to-green-600 px-4 py-2 rounded-full text-white text-sm font-bold animate-pulse">
              AUTO SPEND
            </span>
          </div>
          
          <p className="text-xl md:text-2xl text-white/80 mb-8 max-w-3xl mx-auto">
            Zero Pop-ups. Infinite Giving.
          </p>
          
          {!universalAddress ? (
            <button
              onClick={connectWallet}
              disabled={loading}
              className="bg-green-500 hover:bg-green-600 text-white font-bold py-4 px-8 rounded-2xl text-xl transition-all transform hover:scale-105 disabled:opacity-50 shadow-2xl"
            >
              {loading ? 'Connecting...' : '🔗 Connect Wallet'}
            </button>
          ) : (
            <div className="flex flex-col items-center gap-4">
              <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 inline-block">
                <div className="text-white/80 text-sm">Sub Account</div>
                <div className="text-white font-mono text-lg">
                  {subAccountAddress.slice(0, 6)}...{subAccountAddress.slice(-4)}
                </div>
              </div>
              <button
                onClick={fundSubAccount}
                disabled={loading}
                className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-3 px-6 rounded-xl text-sm transition-all transform hover:scale-105 disabled:opacity-50"
              >
                {loading ? '⏳ Funding...' : '💰 Fund Sub Account (1 USDC)'}
              </button>
              <p className="text-white/60 text-xs max-w-md text-center">
                If donations fail, click above to send 1 USDC to your Sub Account. This helps with gas estimation.
              </p>
            </div>
          )}
        </header>

        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12">
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 text-center">
              <div className="text-3xl font-black text-white mb-1">
                ${parseFloat(stats.total_donated).toFixed(2)}
              </div>
              <div className="text-white/70 text-sm">Total Donated</div>
            </div>
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 text-center">
              <div className="text-3xl font-black text-white mb-1">{stats.total_donors}</div>
              <div className="text-white/70 text-sm">Active Donors</div>
            </div>
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 text-center">
              <div className="text-3xl font-black text-white mb-1">
                {stats.sub_account_donations}
              </div>
              <div className="text-white/70 text-sm">Instant Donations</div>
            </div>
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 text-center">
              <div className="text-3xl font-black text-green-400 mb-1">
                {stats.sub_account_percentage}%
              </div>
              <div className="text-white/70 text-sm">Auto Approved</div>
            </div>
          </div>
        )}

        {/* Status */}
        {status && !showSuccess && (
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 mb-8 text-white text-center whitespace-pre-line">
            {status}
          </div>
        )}

        {/* Campaigns */}
        <div className="text-center mb-8">
          <h2 className="text-4xl font-black text-white mb-4">Active Causes 💝</h2>
          <p className="text-xl text-white/70">Enable auto-spend once, donate instantly forever</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
          {campaigns.map(campaign => (
            <div
              key={campaign.id}
              onClick={() => universalAddress && setSelectedCampaign(campaign)}
              className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 text-white cursor-pointer hover:bg-white/20 transition-all transform hover:scale-105"
            >
              <div className="text-5xl mb-4">{campaign.emoji}</div>
              <h3 className="text-2xl font-bold mb-2">{campaign.title}</h3>
              <p className="text-white/70 mb-4 text-sm">{campaign.description}</p>
              
              <div className="mb-4">
                <div className="flex justify-between text-xs text-white/60 mb-2">
                  <span className="font-bold text-white">
                    ${parseFloat(campaign.raised_amount).toFixed(2)}
                  </span>
                  <span>of ${parseFloat(campaign.goal_amount).toFixed(2)}</span>
                </div>
                <div className="w-full bg-white/20 rounded-full h-3 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-green-400 to-green-600 h-3 rounded-full transition-all"
                    style={{ width: `${Math.min(campaign.progress, 100)}%` }}
                  />
                </div>
              </div>
              
              <button className="w-full bg-green-500 hover:bg-green-600 py-3 rounded-xl font-bold">
                ⚡ Instant Donate
              </button>
            </div>
          ))}
        </div>

        {/* User Donations */}
        {donations.length > 0 && (
          <div className="mb-12">
            <h3 className="text-3xl font-black text-white mb-6 text-center">
              Your Impact History ✨
            </h3>
            <div className="max-w-4xl mx-auto space-y-4">
              {donations.map(donation => (
                <div
                  key={donation.id}
                  className="bg-white/10 backdrop-blur-lg rounded-xl p-4 flex justify-between items-center"
                >
                  <div className="flex items-center gap-4">
                    <div className="text-3xl">{donation.campaign_emoji}</div>
                    <div>
                      <div className="font-bold text-white">{donation.campaign_title}</div>
                      <div className="text-white/60 text-sm">
                        ${parseFloat(donation.amount).toFixed(2)} USDC
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    {donation.used_sub_account && (
                      <div className="bg-green-500 px-3 py-1 rounded-full text-white text-xs font-bold mb-1">
                        ⚡ AUTO
                      </div>
                    )}
                    <div className="text-white/40 text-xs">
                      {donation.tx_hash.slice(0, 12)}...
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Donation Modal */}
        {selectedCampaign && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center p-6 z-50">
            <div className="bg-white/10 backdrop-blur-lg rounded-3xl max-w-lg w-full p-8 text-white relative">
              <button
                onClick={() => setSelectedCampaign(null)}
                className="absolute top-4 right-4 text-white/50 hover:text-white text-3xl leading-none"
              >
                ×
              </button>
              
              <div className="text-center mb-6">
                <div className="text-6xl mb-4">{selectedCampaign.emoji}</div>
                <h3 className="text-2xl font-bold mb-2">{selectedCampaign.title}</h3>
                <p className="text-white/70">{selectedCampaign.description}</p>
              </div>

              <div className="mb-6">
                <label className="block text-lg font-bold mb-3">Amount (USDC)</label>
                <div className="grid grid-cols-4 gap-2 mb-3">
                  {['1', '5', '10', '25'].map(amt => (
                    <button
                      key={amt}
                      onClick={() => setAmount(amt)}
                      className={`py-3 rounded-xl font-bold transition-all ${
                        amount === amt
                          ? 'bg-green-500 scale-105'
                          : 'bg-white/10 hover:bg-white/20'
                      }`}
                    >
                      ${amt}
                    </button>
                  ))}
                </div>
                <input
                  type="number"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="Custom amount"
                  step="0.01"
                  min="0.01"
                  className="w-full rounded-xl px-4 py-3 bg-white/10 border-2 border-white/20 focus:border-green-400 text-white placeholder-white/40 outline-none"
                />
              </div>

              <div className="bg-green-500/20 border border-green-400/50 rounded-2xl p-4 mb-6">
                <div className="flex items-center gap-3">
                  <div className="text-3xl">⚡</div>
                  <div className="text-sm">
                    <strong>First time?</strong> You'll be prompted to allow future payments. 
                    Check "Allow payments for future transactions" to enable instant donations!
                  </div>
                </div>
              </div>

              <button
                onClick={donate}
                disabled={loading || !amount || parseFloat(amount) <= 0}
                className="w-full bg-green-500 hover:bg-green-600 py-4 rounded-2xl font-bold text-xl disabled:opacity-50 transition-all"
              >
                {loading ? '⏳ Processing...' : '💖 Donate Now'}
              </button>

              <div className="mt-4 text-center text-sm text-white/60">
                🛡️ Secured by Base Account SDK
              </div>
            </div>
          </div>
        )}

        {/* Success Modal */}
        {showSuccess && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center p-6 z-50">
            <div className="bg-white/10 backdrop-blur-lg rounded-3xl max-w-md w-full p-8 text-center text-white">
              <div className="w-20 h-20 bg-green-500/30 rounded-full flex items-center justify-center mx-auto mb-6">
                <div className="text-4xl">✅</div>
              </div>
              <h3 className="text-3xl font-black mb-3">Success! 🎉</h3>
              <p className="text-lg text-white/80 mb-6">{successMessage}</p>
              <button
                onClick={() => setShowSuccess(false)}
                className="bg-green-500 hover:bg-green-600 py-3 px-8 rounded-xl font-bold transition-all"
              >
                Continue
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}