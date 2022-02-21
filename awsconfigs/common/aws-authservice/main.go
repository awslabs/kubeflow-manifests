package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"

	"github.com/gorilla/handlers"
	"github.com/gorilla/mux"
)

var port string
var redirectURL string

func init() {
	port = os.Getenv("PORT")
	redirectURL = os.Getenv("LOGOUT_URL")

}

// LogoutHandler expires ALB Cookies and redirects to Cognito Logout Endpoint
func LogoutHandler(w http.ResponseWriter, r *http.Request) {
	log.Println("Traffic reached LogoutHandler")

	// There are 4 possible AWSELBAuthSessionCookies
	for cookieIndex := 0; cookieIndex < 4; cookieIndex++ {
		name := fmt.Sprintf("AWSELBAuthSessionCookie-%s", strconv.Itoa(cookieIndex))
		expireALBCookie := &http.Cookie{Value: "Expired", Name: name, MaxAge: -1, Path: "/"}
		http.SetCookie(w, expireALBCookie)
	}
	http.Redirect(w, r, redirectURL, http.StatusSeeOther)
}

func main() {

	router := mux.NewRouter()
	router.HandleFunc("/logout", LogoutHandler).Methods(http.MethodGet)

	var listenPort = ":" + port
	log.Println("Starting web server at", listenPort)
	log.Fatal(http.ListenAndServe(listenPort, handlers.CORS()(router)))
}
