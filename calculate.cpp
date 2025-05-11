#include <iostream>
using namespace std;

int addNumbers(int a, int b) {
    return a + b;
}

int main() {
    int num1 = 5, num2 = 7;
    cout << "Sum is: " << addNumbers(num1, num2) << endl;
    return 0;
}
