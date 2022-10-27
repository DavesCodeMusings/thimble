These are test scripts for Thimble.

* test_Thimble.py runs unit tests on Thimble class methods.
* mock_api.py runs a mocked-up API on the microcotroller for testing with api_test.
* api_test.py simulates a client machine making requests.

To run the tests, your microcontroller flash filesystem should look like this:

/boot.py
/lib/Thimble.py
/tests/mock_api.py
/tests/test_Thimble.py

boot.py is provded by you and should get your microcontroller connected to the network.

Thimble.py is the Python module under test.

When you run test_Thimble.py it will log the results on the serial console.

When you run mock_api.py, it will create several routes and a /static directory to test
delivery of file-based content. The files shown below will only get created if they do not
exist already.

/static/index.html
/static/testing.txt

While mock_api.py is running on the microcontroller, use another computer to run test_api.py
Test results will be logged on the client computer. The microcontroller serial console will
display debugging information as the tests run.
