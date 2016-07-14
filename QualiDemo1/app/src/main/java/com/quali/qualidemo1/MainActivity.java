package com.quali.qualidemo1;

import android.os.Bundle;
import android.support.design.widget.FloatingActionButton;
import android.support.design.widget.Snackbar;
import android.support.v7.app.AppCompatActivity;
import android.support.v7.widget.Toolbar;
import android.view.View;
import android.view.Menu;
import android.view.MenuItem;
import android.webkit.WebView;
import android.widget.TextView;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;

public class MainActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        Toolbar toolbar = (Toolbar) findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);
        WebView wv = (WebView) findViewById(R.id.webView);
        wv.loadData("Press the button to reload", "text/plain", "UTF-8");
       FloatingActionButton fab = (FloatingActionButton) findViewById(R.id.fab);
        fab.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                WebView wv = (WebView) findViewById(R.id.webView);
                String backendUrl = "http://failed";
                try {
                    BufferedReader reader = new BufferedReader(new InputStreamReader(getAssets().open("backend_url.txt")));
                    String ans="";
                    for(;;) {
                        String line = reader.readLine();
                        if(line == null)
                            break;
                        ans += line + "\n";
                    }
                    backendUrl = ans.trim().split("\n")[0].trim();
                    wv.loadUrl(backendUrl);
                    ((TextView)findViewById(R.id.textView)).setText(backendUrl);
                } catch (IOException e) {
                    StringBuilder sb = new StringBuilder();
                    sb.append(e.toString() + "\n");
                    for (StackTraceElement el : e.getStackTrace()) {
                        sb.append(el.toString() + "\n");
                    }
                    wv.loadData(sb.toString(), "text/plain", "UTF-8");

                    e.printStackTrace();
                }
                Snackbar.make(view, "Requested '" + backendUrl + "'", Snackbar.LENGTH_LONG).setAction("Action", null).show();
            }
        });
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        // Inflate the menu; this adds items to the action bar if it is present.
        getMenuInflater().inflate(R.menu.menu_main, menu);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        // Handle action bar item clicks here. The action bar will
        // automatically handle clicks on the Home/Up button, so long
        // as you specify a parent activity in AndroidManifest.xml.
        int id = item.getItemId();

        //noinspection SimplifiableIfStatement
        if (id == R.id.action_settings) {
            return true;
        }

        return super.onOptionsItemSelected(item);
    }
}
