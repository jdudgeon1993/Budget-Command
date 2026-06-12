
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_902629b99766986af69c75415059ff69 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_85d27e9aeefd218c061f729fb0e74aac = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.go_prev_month", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["cursor"] : "pointer", ["color"] : "#4e4e6a", ["padding"] : "4px 8px", ["borderRadius"] : "6px", ["&:hover"] : ({ ["color"] : "#818cf8", ["background"] : "#1c1c25" }) }),onClick:on_click_85d27e9aeefd218c061f729fb0e74aac},children)
    )
});
