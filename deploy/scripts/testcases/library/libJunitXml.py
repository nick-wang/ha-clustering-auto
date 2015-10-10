#!/usr/bin/python

from junit_xml import TestSuite, TestCase

def assertCase(testcase, func, conf=None):
    result = func(conf)
    if not result["pass"]:
        testcase.add_error_info(result["message"], result['output'])
    elif result["skip"]:
        testcase.add_skipped_info(result["message"], result['output'])
    if result["skipall"]:
        return True
    return False

def skipCase(testcase, message, output=None):
    testcase.add_skipped_info(message, output)

def _exampleFunc(temp):
    result = {"pass":False, "message":"", "output":""}

    #Own test steps

    #Test OK
    if temp:
        result["pass"] = True
        return result
    #Test NG
    else:
        result["message"] = "Test failed!"
        result["output"] = "No more space in sda."
        return result

def _test():
    test_case1 = TestCase('Testname1', 'SetupCluster.Name')
    test_case2 = TestCase('Testname2', 'SetupCluster.Name')
    test_case3 = TestCase('Testname3', 'SetupCluster.Misc')
    test_case4 = TestCase('Testname4', 'SetupCluster.Misc')

    test_cases = [test_case1, test_case2, test_case3, test_case4]
    ts = TestSuite("My Test Suite", test_cases)

    #Run and verify test case
    assertCase(test_case1, _exampleFunc(True))
    assertCase(test_case2, _exampleFunc(False))
    assertCase(test_case3, _exampleFunc(True))
    #Skip test case
    skipCase(test_case4, "Skip Testname4.", "Testname2 is failed.")

    print(ts.to_xml_string([ts]))

    #with open('output.xml', 'w') as f:
    #    ts.to_file(f, [ts])

if __name__ == "__main__":
    '''
        This is a library to test and output in junit xml for jenkins.
    '''
    _test()
