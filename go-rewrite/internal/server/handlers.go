package server

import (
	"log"
	"net/http"
	"time"
)

// corsMiddleware adds CORS headers to responses
func (s *Server) corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Set CORS headers
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
		w.Header().Set("Access-Control-Max-Age", "86400")

		// Handle preflight requests
		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}

		next.ServeHTTP(w, r)
	})
}

// loggingMiddleware logs HTTP requests
func (s *Server) loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		// Create a response writer wrapper to capture status code
		wrapper := &responseWriter{ResponseWriter: w, statusCode: http.StatusOK}

		next.ServeHTTP(wrapper, r)

		duration := time.Since(start)
		log.Printf("%s %s %d %v %s",
			r.Method,
			r.RequestURI,
			wrapper.statusCode,
			duration,
			r.RemoteAddr,
		)
	})
}

// responseWriter wraps http.ResponseWriter to capture status code
type responseWriter struct {
	http.ResponseWriter
	statusCode int
}

func (rw *responseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

// authMiddleware provides basic authentication (if needed)
func (s *Server) authMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Skip authentication for health check and public endpoints
		if r.URL.Path == "/api/v1/health" || r.URL.Path == "/" || r.URL.Path == "/network_topology.html" {
			next.ServeHTTP(w, r)
			return
		}

		// For now, no authentication required
		// This can be extended to support API keys, OAuth, etc.
		next.ServeHTTP(w, r)
	})
}

// rateLimitMiddleware provides basic rate limiting (if needed)
func (s *Server) rateLimitMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// For now, no rate limiting
		// This can be extended to implement rate limiting logic
		next.ServeHTTP(w, r)
	})
}

// securityHeadersMiddleware adds security headers
func (s *Server) securityHeadersMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Add security headers
		w.Header().Set("X-Content-Type-Options", "nosniff")
		w.Header().Set("X-Frame-Options", "DENY")
		w.Header().Set("X-XSS-Protection", "1; mode=block")
		w.Header().Set("Referrer-Policy", "strict-origin-when-cross-origin")

		// For HTML responses, add CSP header
		if r.URL.Path == "/" || r.URL.Path == "/network_topology.html" {
			w.Header().Set("Content-Security-Policy", 
				"default-src 'self'; "+
				"script-src 'self' 'unsafe-inline' https://unpkg.com; "+
				"style-src 'self' 'unsafe-inline'; "+
				"img-src 'self' data:; "+
				"connect-src 'self'")
		}

		next.ServeHTTP(w, r)
	})
}

// compressionMiddleware adds gzip compression (basic implementation)
func (s *Server) compressionMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// For now, no compression
		// This can be extended to implement gzip compression
		next.ServeHTTP(w, r)
	})
}

// healthCheckHandler provides a simple health check endpoint
func (s *Server) healthCheckHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"status":"ok","timestamp":"` + time.Now().UTC().Format(time.RFC3339) + `"}`))
}

// notFoundHandler handles 404 errors
func (s *Server) notFoundHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusNotFound)
	w.Write([]byte(`{"error":"Not Found","message":"The requested resource was not found"}`))
}

// methodNotAllowedHandler handles 405 errors
func (s *Server) methodNotAllowedHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusMethodNotAllowed)
	w.Write([]byte(`{"error":"Method Not Allowed","message":"The request method is not allowed for this resource"}`))
}

// internalServerErrorHandler handles 500 errors
func (s *Server) internalServerErrorHandler(w http.ResponseWriter, r *http.Request, err error) {
	log.Printf("Internal server error: %v", err)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusInternalServerError)
	w.Write([]byte(`{"error":"Internal Server Error","message":"An internal server error occurred"}`))
}

// setupErrorHandlers configures error handlers for the router
func (s *Server) setupErrorHandlers() {
	s.router.NotFoundHandler = http.HandlerFunc(s.notFoundHandler)
	s.router.MethodNotAllowedHandler = http.HandlerFunc(s.methodNotAllowedHandler)
}
