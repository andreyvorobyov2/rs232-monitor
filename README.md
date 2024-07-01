# python-RS232-monitor

This is a monitor for RS-232 port

![Screenshot](screenshot.png?raw=true)

## Installation

```
pip install -r requirements.txt
```

For GUI used [GTK 3.0](https://www.gtk.org/) 
### Linux

```
sudo apt install libcairo2-dev
sudo apt install libgirepository1.0-dev
```
### Windows and other

install [PyGObject](https://pygobject.gnome.org/getting_started.html)


## usage Arduino
more example [sketch](https://docs.arduino.cc/software/ide-v2/tutorials/ide-v2-serial-plotter/#example-sketch)
```cpp
void setup() {
  Serial.begin(9600);
}
void loop() {
  for (float i = 0; i < 360; i += 1) {
    float Sine1 = 100 * sin(i * M_PI / 180);
    Serial.println(Sine1);
    delay(10);
  }
}
```