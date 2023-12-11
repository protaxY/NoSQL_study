package my_logger

import (
	"fmt"
	"os"

	"github.com/withmandala/go-log"
)

type myLogger struct {
	logIntoFile   *log.Logger
	logIntoConsol *log.Logger
}

func (l *myLogger) Error(v ...interface{}) {
	l.logIntoConsol.Error(v...)
	l.logIntoFile.Error(v...)
}
func (l *myLogger) Errorf(format string, v ...interface{}) {
	l.logIntoConsol.Errorf(format, v...)
	l.logIntoFile.Errorf(format, v...)
}
func (l *myLogger) Info(v ...interface{}) {
	l.logIntoConsol.Info(v...)
	l.logIntoFile.Info(v...)
}
func (l *myLogger) Infof(format string, v ...interface{}) {
	l.logIntoConsol.Infof(format, v...)
	l.logIntoFile.Infof(format, v...)
}

var LoggerVar myLogger

func init() {
	f, err := os.Create("app.log")
	if err != nil {
		fmt.Println("cant open log file")
		os.Exit(1)
	}
	LoggerVar = myLogger{
		logIntoFile:   log.New(f).WithoutColor(),
		logIntoConsol: log.New(os.Stderr).WithColor(),
	}

}
