package api

import (
	"context"
	"crypto/rand"
	"encoding/base64"
	"fmt"
	"net/http"
	"net/url"
	"time"

	"golang.org/x/oauth2"
)

// OAuthConfig holds OAuth configuration for Tailscale API
type OAuthConfig struct {
	ClientID     string
	ClientSecret string
	RedirectURL  string
	Scopes       []string
}

// OAuthHelper provides OAuth authentication flow helpers
type OAuthHelper struct {
	config *oauth2.Config
}

// NewOAuthHelper creates a new OAuth helper
func NewOAuthHelper(cfg *OAuthConfig) *OAuthHelper {
	config := &oauth2.Config{
		ClientID:     cfg.ClientID,
		ClientSecret: cfg.ClientSecret,
		RedirectURL:  cfg.RedirectURL,
		Scopes:       cfg.Scopes,
		Endpoint: oauth2.Endpoint{
			AuthURL:  "https://api.tailscale.com/api/v2/oauth/authorize",
			TokenURL: "https://api.tailscale.com/api/v2/oauth/token",
		},
	}

	return &OAuthHelper{
		config: config,
	}
}

// GetAuthURL generates an OAuth authorization URL
func (h *OAuthHelper) GetAuthURL(state string) string {
	return h.config.AuthCodeURL(state, oauth2.AccessTypeOffline)
}

// GenerateState generates a random state parameter for OAuth
func (h *OAuthHelper) GenerateState() (string, error) {
	b := make([]byte, 32)
	if _, err := rand.Read(b); err != nil {
		return "", fmt.Errorf("failed to generate random state: %w", err)
	}
	return base64.URLEncoding.EncodeToString(b), nil
}

// ExchangeCode exchanges an authorization code for tokens
func (h *OAuthHelper) ExchangeCode(ctx context.Context, code string) (*oauth2.Token, error) {
	token, err := h.config.Exchange(ctx, code)
	if err != nil {
		return nil, fmt.Errorf("failed to exchange code for token: %w", err)
	}
	return token, nil
}

// RefreshToken refreshes an OAuth token
func (h *OAuthHelper) RefreshToken(ctx context.Context, token *oauth2.Token) (*oauth2.Token, error) {
	tokenSource := h.config.TokenSource(ctx, token)
	newToken, err := tokenSource.Token()
	if err != nil {
		return nil, fmt.Errorf("failed to refresh token: %w", err)
	}
	return newToken, nil
}

// CreateHTTPClient creates an HTTP client with OAuth token
func (h *OAuthHelper) CreateHTTPClient(ctx context.Context, token *oauth2.Token) *http.Client {
	return h.config.Client(ctx, token)
}

// ValidateToken validates an OAuth token
func (h *OAuthHelper) ValidateToken(token *oauth2.Token) error {
	if token == nil {
		return fmt.Errorf("token is nil")
	}

	if token.AccessToken == "" {
		return fmt.Errorf("access token is empty")
	}

	if token.Expiry.Before(time.Now()) {
		return fmt.Errorf("token has expired")
	}

	return nil
}

// OAuthServer provides a simple OAuth callback server
type OAuthServer struct {
	server   *http.Server
	codeChan chan string
	errChan  chan error
	state    string
}

// NewOAuthServer creates a new OAuth callback server
func NewOAuthServer(port int, expectedState string) *OAuthServer {
	mux := http.NewServeMux()
	server := &http.Server{
		Addr:    fmt.Sprintf(":%d", port),
		Handler: mux,
	}

	oauthServer := &OAuthServer{
		server:   server,
		codeChan: make(chan string, 1),
		errChan:  make(chan error, 1),
		state:    expectedState,
	}

	mux.HandleFunc("/callback", oauthServer.handleCallback)
	mux.HandleFunc("/", oauthServer.handleRoot)

	return oauthServer
}

// Start starts the OAuth callback server
func (s *OAuthServer) Start() error {
	go func() {
		if err := s.server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			s.errChan <- fmt.Errorf("server error: %w", err)
		}
	}()
	return nil
}

// Stop stops the OAuth callback server
func (s *OAuthServer) Stop(ctx context.Context) error {
	return s.server.Shutdown(ctx)
}

// WaitForCode waits for the OAuth authorization code
func (s *OAuthServer) WaitForCode(timeout time.Duration) (string, error) {
	select {
	case code := <-s.codeChan:
		return code, nil
	case err := <-s.errChan:
		return "", err
	case <-time.After(timeout):
		return "", fmt.Errorf("timeout waiting for OAuth callback")
	}
}

// handleCallback handles the OAuth callback
func (s *OAuthServer) handleCallback(w http.ResponseWriter, r *http.Request) {
	query := r.URL.Query()
	
	// Check for error
	if errMsg := query.Get("error"); errMsg != "" {
		errDesc := query.Get("error_description")
		s.errChan <- fmt.Errorf("OAuth error: %s - %s", errMsg, errDesc)
		http.Error(w, "OAuth authorization failed", http.StatusBadRequest)
		return
	}

	// Validate state
	state := query.Get("state")
	if state != s.state {
		s.errChan <- fmt.Errorf("invalid state parameter")
		http.Error(w, "Invalid state parameter", http.StatusBadRequest)
		return
	}

	// Get authorization code
	code := query.Get("code")
	if code == "" {
		s.errChan <- fmt.Errorf("no authorization code received")
		http.Error(w, "No authorization code received", http.StatusBadRequest)
		return
	}

	// Send success response
	w.Header().Set("Content-Type", "text/html")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`
		<!DOCTYPE html>
		<html>
		<head>
			<title>OAuth Success</title>
			<style>
				body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
				.success { color: green; font-size: 24px; }
				.message { color: #666; margin-top: 20px; }
			</style>
		</head>
		<body>
			<div class="success">✅ Authorization Successful!</div>
			<div class="message">You can now close this window and return to the application.</div>
		</body>
		</html>
	`))

	// Send code to channel
	s.codeChan <- code
}

// handleRoot handles requests to the root path
func (s *OAuthServer) handleRoot(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/html")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`
		<!DOCTYPE html>
		<html>
		<head>
			<title>OAuth Callback Server</title>
			<style>
				body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
				.info { color: #666; font-size: 18px; }
			</style>
		</head>
		<body>
			<div class="info">OAuth callback server is running...</div>
			<div class="info">Waiting for authorization callback.</div>
		</body>
		</html>
	`))
}

// InteractiveOAuthFlow performs an interactive OAuth flow
func InteractiveOAuthFlow(cfg *OAuthConfig) (*oauth2.Token, error) {
	helper := NewOAuthHelper(cfg)

	// Generate state
	state, err := helper.GenerateState()
	if err != nil {
		return nil, fmt.Errorf("failed to generate state: %w", err)
	}

	// Parse redirect URL to get port
	redirectURL, err := url.Parse(cfg.RedirectURL)
	if err != nil {
		return nil, fmt.Errorf("invalid redirect URL: %w", err)
	}

	port := 8080 // default port
	if redirectURL.Port() != "" {
		port = 8080 // use parsed port if available
	}

	// Start callback server
	server := NewOAuthServer(port, state)
	if err := server.Start(); err != nil {
		return nil, fmt.Errorf("failed to start callback server: %w", err)
	}
	defer server.Stop(context.Background())

	// Get authorization URL
	authURL := helper.GetAuthURL(state)
	fmt.Printf("Please visit the following URL to authorize the application:\n%s\n", authURL)

	// Wait for callback
	code, err := server.WaitForCode(5 * time.Minute)
	if err != nil {
		return nil, fmt.Errorf("failed to get authorization code: %w", err)
	}

	// Exchange code for token
	ctx := context.Background()
	token, err := helper.ExchangeCode(ctx, code)
	if err != nil {
		return nil, fmt.Errorf("failed to exchange code for token: %w", err)
	}

	return token, nil
}
