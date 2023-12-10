package main

import (
	"context"
	"os"
	"os/signal"
	"syscall"

	"github.com/protaxY/NoSQL_study/dumps/my_logger"
	"github.com/protaxY/NoSQL_study/dumps/parsers"
	"github.com/protaxY/NoSQL_study/dumps/requests"
)

// хотим ли мы залить пользователей
const readUsers = false

func main() {
	ctx, cancel := context.WithCancel(context.Background())

	interaptKeyChan := make(chan os.Signal, 1)
	signal.Notify(interaptKeyChan, os.Interrupt, syscall.SIGTERM)
	go func() {
		<-interaptKeyChan
		cancel()
		my_logger.LoggerVar.Info("Key interrapt has been triggered")
	}()

	if readUsers {
		users, err := parsers.JsonParser[parsers.UserDataSet]("./users_data_set.json")
		if err != nil {
			my_logger.LoggerVar.Error(err)
			return
		}

		result := requests.LoadUsers(ctx, users)

		err = parsers.JsonSaver[parsers.UserDataSet]("./users_result.json", result)
		if err != nil {
			my_logger.LoggerVar.Error(err)
			return
		}
	} else {
		usersWithMongoIDs, err := parsers.JsonParser[parsers.UserDataSetWithoutData]("./users_result.json")
		if err != nil {
			my_logger.LoggerVar.Error(err)
			return
		}
		messagesDataSet, err := parsers.JsonParser[[]parsers.MsgDataSet]("./msg_data_set.json")
		if err != nil {
			my_logger.LoggerVar.Error(err)
			return
		}

		my_logger.LoggerVar.Info("Starting to send messages...")
		requests.LoadMessages(ctx, usersWithMongoIDs, messagesDataSet)

	}
}
