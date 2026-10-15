For the agent we built we want to have a canvas app, which is a free flowing canvas and becomes the medium of learning for a child

 - Teacher can write on canvas, annotate child's work, can speak while annotating or writing. 
 - Child can also write back, or speak back to teacher

In past we have experimented with tldraw and seems to be a good way to build. A poc project for this is present in /Users/ashishjain/Documents/Code/fluento/prodigy-canvas-poc. Can be used for reference only
 - How it draw diagrams
 - How it annotated back

we would build a websocket transport, or a webrtc transport which will be used by the canvas to connect to and then render or send back data (text/image/audio)

from server/transport to canvas, we would get series of events like
 - text
 - speech
 - diagram
 - draw
 - play
 - ask

which could be used by canvas to draw things accordingly on canvas

from server side one possibility could be to define above as output modularities and pass them while loading session

for ex, 

node scripts/cli.mjs \
    --concept graphing-solutions-to-2-variable-linear-equations-1 \
    --student weak-student --log-level none --output canvas 
    
canvas as a modulaity can be a separate class, which can be called while stitching prompts and it explains how the response should be written. Mostly the response should be of type yaml

ex:

speak: Lets start with this equation
write: 5x - 2 = 3
speak: what do you think is the value of x in this?

speak: What is the area of below figure
draw: 
 - type: diagram
 - shape: <>
speak: what figure is this? how do you calculate its area?

and same is used as a parser before piping it to transport. Parser is an eager parser and try to match things as it can, and then pass the same o/p to transport

ex below code in session manager might change to:

```
transport.on('message', async (text) => {

  try {

     for await (const event of agent.send(text)) {

         transport.handle(event);

      }

      persistSession(agent.ctx).catch(() => {});

  } catch (err) {

      transport.handle({ type: 'error', message: String(err) });

  }
});
```

```
transport.on('message', async (text) => {

  try {

     for await (const event of agent.send(text)) {

         // by default output is as-is, yields the same event back
         // if output is canvas, as it gets
         //   text: yield
         //   speak: give it to tts service, emit chunks of audio as they come
         //   play: return json of video url
         //   draw: yield diagram definition
         for await (const result of output.parse(event)) {
             transport.handle(result);
         }
      }

      persistSession(agent.ctx).catch(() => {});

  } catch (err) {

      transport.handle({ type: 'error', message: String(err) });

  }
});
```