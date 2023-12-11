package requests

import (
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"sync"
	"time"

	"github.com/protaxY/NoSQL_study/dumps/my_logger"
	"github.com/protaxY/NoSQL_study/dumps/parsers"
	"github.com/schollz/progressbar/v3"
)

func createUserReq(wg *sync.WaitGroup, host string, readUserDataChan <-chan parsers.UserDataMapFormated, writeUseraDataChan chan parsers.UserDataMapFormated, workerCount int) {
	defer wg.Done()
	method := "POST"
	client := &http.Client{}
	my_logger.LoggerVar.Infof("craeting %d worker", workerCount)

	for userData := range readUserDataChan {
		params := url.Values{}
		params.Add("username", userData.UserData.UserName)
		params.Add("name", userData.UserData.UserName)
		params.Add("timestamp", time.Time(userData.UserData.CreationDate).Format(parsers.IsoformatLayout))
		url := fmt.Sprintf("%s?%s", host, params.Encode())

		req, err := http.NewRequest(method, url, nil)
		if err != nil {
			my_logger.LoggerVar.Errorf("User cant be added due request error [userName=%s, userID=%s]: %s", userData.UserData.UserName, userData.UserID, err.Error())
			continue
		}

		res, err := client.Do(req)
		if err != nil {
			my_logger.LoggerVar.Errorf("User cant be added due request DO error [userName=%s, userID=%s]: %s", userData.UserData.UserName, userData.UserID, err.Error())
			continue
		}

		if res.StatusCode != http.StatusOK {
			body, err := io.ReadAll(res.Body)
			if err != nil {
				my_logger.LoggerVar.Errorf("cannot ready body while getting status code %d [userName=%s, userID=%s]: %s", res.StatusCode, userData.UserData.UserName, userData.UserID, err.Error())
				res.Body.Close()
				continue
			}
			my_logger.LoggerVar.Errorf("status code %d [userName=%s, userID=%s]\nBody: %s", res.StatusCode, userData.UserData.UserName, userData.UserID, body)
			res.Body.Close()
			continue
		}

		body, err := io.ReadAll(res.Body)
		if err != nil {
			my_logger.LoggerVar.Errorf("cannot ready body [userName=%s, userID=%s]: %s", userData.UserData.UserName, userData.UserID, err.Error())
			res.Body.Close()
			continue
		}

		// prepare to send to channel
		userData.UserData.MongoUserID = strings.Trim(string(body), "\"")
		res.Body.Close()

		writeUseraDataChan <- userData
	}

	my_logger.LoggerVar.Infof("readUserDataChan has been closed. Turning off worker %d...", workerCount)
}

func workerReader(wg *sync.WaitGroup, progressbar *progressbar.ProgressBar, writeUseraDataChan <-chan parsers.UserDataMapFormated) parsers.UserDataSet {
	result := make(parsers.UserDataSet)
	defer wg.Done()

	for userData := range writeUseraDataChan {
		result[userData.UserID] = userData.UserData
		progressbar.Add(1)

	}
	my_logger.LoggerVar.Info("writeUseraDataChan has been closed. Turning off worderReader...")
	return result
}
