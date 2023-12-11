package requests

import (
	"context"
	"sync"

	"github.com/protaxY/NoSQL_study/dumps/my_logger"
	"github.com/protaxY/NoSQL_study/dumps/parsers"
	"github.com/schollz/progressbar/v3"
)

const (
	workersCount = 100
)

func LoadUsers(ctx context.Context, users parsers.UserDataSet) parsers.UserDataSet {
	// start workers
	readUserDataChan := make(chan parsers.UserDataMapFormated, workersCount)
	writeUseraDataChan := make(chan parsers.UserDataMapFormated)
	var (
		wgReader      sync.WaitGroup
		wgSender      sync.WaitGroup
		result        parsers.UserDataSet
		bar           = progressbar.Default(int64(len(users)), "status")
		channelClosed bool
	)

	for i := 0; i < workersCount; i++ {
		wgSender.Add(1)
		go createUserReq(&wgSender, "http://localhost/messenger/users", readUserDataChan, writeUseraDataChan, i)
	}

	wgReader.Add(1)
	go func() {
		result = workerReader(&wgReader, bar, writeUseraDataChan)
	}()

L:
	for userID, userData := range users {
		select {
		case <-ctx.Done():
			my_logger.LoggerVar.Info("Canceling intration")
			close(readUserDataChan)
			my_logger.LoggerVar.Info("waiting for workers to complite tasks...")
			wgSender.Wait()
			close(writeUseraDataChan)
			wgReader.Wait()
			channelClosed = true
			break L
		default:
			userDataToSend := parsers.UserDataMapFormated{
				UserID:   userID,
				UserData: userData,
			}

			readUserDataChan <- userDataToSend
		}
	}

	if !channelClosed {
		close(readUserDataChan)
		my_logger.LoggerVar.Info("waiting for workers to complite tasks...")
		wgSender.Wait()
		close(writeUseraDataChan)
		wgReader.Wait()
	}

	return result
}

func LoadMessages(ctx context.Context, usersDataSet parsers.UserDataSetWithoutData, messageDataSet []parsers.MsgDataSet) {
	// start workers
	readMsgDataChan := make(chan parsers.MsgDataSet, workersCount)
	var (
		wgSender      sync.WaitGroup
		bar           = progressbar.Default(int64(len(messageDataSet)), "status")
		channelClosed bool
	)

	for i := 0; i < workersCount; i++ {
		wgSender.Add(1)
		go createMessageReq(&wgSender, bar, "http://localhost/messenger/users", readMsgDataChan, i)
	}

L:
	for _, msgData := range messageDataSet {
		select {
		case <-ctx.Done():
			my_logger.LoggerVar.Info("Canceling intration")
			close(readMsgDataChan)
			my_logger.LoggerVar.Info("waiting for workers to complite tasks...")
			wgSender.Wait()
			channelClosed = true
			break L
		default:
			// skipping message without users in out database
			fromUserData, ok := usersDataSet[msgData.FromUser]
			if !ok {
				continue
			}
			toUserData, ok := usersDataSet[msgData.ToUser]
			if !ok {
				continue
			}

			msgData.FromUser = fromUserData.MongoUserID
			msgData.ToUser = toUserData.MongoUserID

			readMsgDataChan <- msgData
		}
	}

	if !channelClosed {
		close(readMsgDataChan)
		my_logger.LoggerVar.Info("waiting for workers to complite tasks...")
		wgSender.Wait()
	}
}
