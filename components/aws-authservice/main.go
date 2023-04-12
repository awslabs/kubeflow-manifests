// Copyright Amazon.com Inc. or its affiliates. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License"). You may
// not use this file except in compliance with the License. A copy of the
// License is located at
//
//     http://aws.amazon.com/apache2.0/
//
// or in the "license" file accompanying this file. This file is distributed
// on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
// express or implied. See the License for the specific language governing
// permissions and limitations under the License.

package main

import (
	"encoding/json"
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
	port = "8082"
	redirectURL = os.Getenv("LOGOUT_URL")

}

// LogoutHandler expires ALB Cookies and redirects to Cognito Logout Endpoint
func LogoutHandler(w http.ResponseWriter, r *http.Request) {
	log.Println("Traffic reached LogoutHandler")
	// There are 4 possible AWSELBAuthSessionCookies
	// https://docs.aws.amazon.com/elasticloadbalancing/latest/application/listener-authenticate-users.html#authentication-logout
	for cookieIndex := 0; cookieIndex < 4; cookieIndex++ {
		name := fmt.Sprintf("AWSELBAuthSessionCookie-%s", strconv.Itoa(cookieIndex))
		expireALBCookie := &http.Cookie{Value: "Expired", Name: name, MaxAge: -1, Path: "/"}
		http.SetCookie(w, expireALBCookie)
	}

	// Central Dashboard expects to redirect to event.detail.response['afterLogoutURL']) after logout
	// https://github.com/kubeflow/kubeflow/blob/master/components/centraldashboard/public/components/logout-button.js#L49
	resp := struct {
		AfterLogoutURL string `json:"afterLogoutURL"`
	}{
		AfterLogoutURL: redirectURL,
	}
	jsonBytes, err := json.Marshal(resp)
	if err != nil {
		log.Println("Failed to marshal struct to json: %v", err)
	}

	w.Write(jsonBytes)

	http.Redirect(w, r, redirectURL, http.StatusCreated)
}

func main() {

	router := mux.NewRouter()
	router.HandleFunc("/authservice/logout", LogoutHandler).Methods(http.MethodPost)
	var listenPort = ":" + port
	log.Println("Starting web server at", listenPort)
	log.Println(http.ListenAndServe(listenPort, handlers.CORS()(router)))
}
