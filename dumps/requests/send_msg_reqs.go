package requests

import (
	"encoding/json"
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

type SendMsgBodyReq struct {
	TextContent string `json:"text_content"`
}

func createMessageReq(wg *sync.WaitGroup, progressbar *progressbar.ProgressBar, host string, msgReadChan <-chan parsers.MsgDataSet, workerCount int) {
	defer wg.Done()

	client := &http.Client{}
	my_logger.LoggerVar.Infof("craeting %d worker", workerCount)

	for message := range msgReadChan {

		params := url.Values{}
		params.Add("timestamp", time.Time(message.CreationDate).Format(parsers.IsoformatLayout))
		url := fmt.Sprintf("%s/%s/chats/%s", host, message.FromUser, message.ToUser)
		payload := SendMsgBodyReq{
			TextContent: message.Message,
		}
		reqBody, err := json.Marshal(payload)
		if err != nil {
			my_logger.LoggerVar.Errorf("cannot marshal message body [from=%s to=%s]: %s", message.FromUser, message.ToUser, err.Error())
			continue
		}

		req, err := http.NewRequest(http.MethodPost, url, strings.NewReader(string(reqBody)))
		if err != nil {
			my_logger.LoggerVar.Errorf("Message cant be sent due request error [from=%s to=%s]: %s", message.FromUser, message.ToUser, err.Error())
			continue
		}

		res, err := client.Do(req)
		if err != nil {
			my_logger.LoggerVar.Errorf("Message cant be sent due request DO error [from=%s to=%s]: %s", message.FromUser, message.ToUser, err.Error())
			continue
		}

		if res.StatusCode != http.StatusOK {
			body, err := io.ReadAll(res.Body)
			if err != nil {
				my_logger.LoggerVar.Errorf("cannot ready body while getting status code %d [from=%s to=%s]: %s", res.StatusCode, message.FromUser, message.ToUser, err.Error())
				res.Body.Close()
				continue
			}
			my_logger.LoggerVar.Errorf("status code %d [from=%s to=%s]\nBody: %s", res.StatusCode, message.FromUser, message.ToUser, body)
			res.Body.Close()
			continue
		}

		res.Body.Close()
		progressbar.Add(1)
	}

	my_logger.LoggerVar.Infof("msgReadChan has been closed. Turning off worker %d...", workerCount)
}
