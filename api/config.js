// Vercel Serverless Function to deliver runtime environment configuration to static frontend
module.exports = (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Cache-Control', 's-maxage=60, stale-while-revalidate');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  return res.status(200).json({
    api_base_url: process.env.API_BASE_URL || '',
    environment: process.env.VERCEL_ENV || 'production',
    region: process.env.VERCEL_REGION || 'edge'
  });
};
