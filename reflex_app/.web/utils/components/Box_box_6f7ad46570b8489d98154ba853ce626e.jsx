
import {Fragment,memo,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_6f7ad46570b8489d98154ba853ce626e = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);

                useEffect(() => {
                    ((...args) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.on_dashboard_load", ({  }), ({  })))], args, ({  }))))()
                    return () => {
                        
                    }
                }, []);



    return(
        jsx(RadixThemesBox,{css:({ ["background"] : "#0c0c10", ["color"] : "#f0f0fa", ["fontFamily"] : "Rajdhani, system-ui, sans-serif", ["--default-font-family"] : "Rajdhani, system-ui, sans-serif", ["minHeight"] : "100vh" })},children)
    )
});
