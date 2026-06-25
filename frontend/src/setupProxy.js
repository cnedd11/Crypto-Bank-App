const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // log so we know it's loaded
  console.log('» setupProxy is in use');

  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:5000',
      changeOrigin: true,
    })
  );
};
